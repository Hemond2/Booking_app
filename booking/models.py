import uuid
from django.db import models
from datetime import time
from django.core.exceptions import ValidationError
from django.utils import timezone

class SzakmaIrany(models.Model):
    nev = models.CharField(max_length=255, unique=True)
    leiras = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.nev


class Kliens(models.Model):
    kliens_azonosito = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    nev = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    telefon = models.CharField(max_length=30, blank=True, null=True)
    vallalat = models.CharField(max_length=255, blank=True, null=True)
    letrehozva = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.nev} {self.vallalat} {self.telefon} {self.email}"

class Konzultans(models.Model):
    konzultans_azonosito = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    nev = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    szakirany = models.ForeignKey(
        SzakmaIrany,
        on_delete=models.PROTECT,
        related_name = 'konzultansok'
    )

    # Alap munkaidő: 09:00 - 17:00
    munka_kezdes = models.TimeField(default=time(9, 0))
    munka_befejezes = models.TimeField(default=time(17, 0))
    aktiv = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.nev} - {self.szakirany.nev}"

    def elerhetoseg_osszegzes(self, cel_datum=None):
        """
        Segédmetódus a szabad/foglalt időpontok kiszámításához a felhasználói felületen.
        """
        if cel_datum is None:
            cel_datum = timezone.now().date()

        nap_kezdet = timezone.make_aware(
            timezone.datetime.combine(cel_datum, self.munka_kezdes)
        )
        nap_vege = timezone.make_aware(
            timezone.datetime.combine(cel_datum, self.munka_befejezes)
        )

        # Az összes elfogadott találkozó lekérése a céldátumhoz
        foglalas = self.idopontok.filter(
            kezdes__lt = nap_vege,
            vege__gt = nap_kezdet,
            statusz__in = ['FÜGGŐ', 'IGAZOLT']
        ).order_by('kezdes')

        foglalt_idopontok = [
            {
                "kezdes": appt.kezdes.strftime("%H:%M"),
                "vege": appt.vege.strftime("%H:%M")
            }
            for appt in foglalas
        ]

        return {
            "konzultans_azonosito": str(self.konzultans_azonosito),  
            "konzultans_nev": self.nev,  
            "szakirany": self.szakirany.nev,  
            "datum": cel_datum.isoformat(),  
            "munkaido": f"{self.munka_kezdes.strftime('%H:%M')} - {self.munka_befejezes.strftime('%H:%M')}", 
            "foglalasok_szama": len(foglalt_idopontok),  
            "foglalt_idopontok": foglalt_idopontok,  
            "teljesen_foglalt": len(foglalt_idopontok) >= 4,  
        }

class Idopontok(models.Model):
    STATUSZOK = [
        ("FÜGGŐ", "Függő"),
        ("IGAZOLT", "Igazolt"),
        ("VISSZAVONT", "Visszavont"),
    ]

    idopont_azonosito = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    kliens = models.ForeignKey(Kliens, on_delete=models.CASCADE, related_name='idopontok')
    konzultans = models.ForeignKey(Konzultans, on_delete=models.CASCADE, related_name='idopontok')
    szakirany = models.ForeignKey(SzakmaIrany, on_delete=models.PROTECT)

    kezdes = models.DateTimeField()
    vege = models.DateTimeField()
    statusz = models.CharField(max_length=20, choices=STATUSZOK, default='CONFIRMED')
    letrehozva = models.DateTimeField(auto_now_add=True)

    def clean(self):
        """Logika a dupla foglalások és az érvénytelen időpontok megelőzésére."""
        if self.kezdes and self.vege:
            if self.kezdes >= self.vege:
                raise ValidationError("A kezdésnek a véghe előtt kell lenni.")
            # Dupla foglás átfedésének ellenőrzése
            atfedes = Idopontok.objects.filter(
                konzultans=self.konzultans,
                statusz__in = ["FÜGGŐ", "IGAZOLT"],
                kezdes__lt = self.vege,
                vege__gt = self.kezdes
            )

            if self.pk:
                atfedes = atfedes.exclude(pk=self.pk)

            if atfedes.exists():
                raise ValidationError("A konzultáns már foglalt ebben az időpontban.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.konzultans.nev} with {self.kliens.nev} @ {self.kezdes.strftime('%Y-%m-%d %H:%M')}"