from rest_framework import serializers
from django.utils import timezone
from .models import SzakmaIrany, Kliens, Konzultans, Idopontok

class SzakmaIranySerializer(serializers.ModelSerializer):
    class Meta:
        model = SzakmaIrany
        fields = ['id', 'nev', 'leiras']

class KliensSerializer(serializers.ModelSerializer):
    class Meta:
        model = Kliens
        fields = ['kliens_azonosito', 'nev', 'email', 'telefon', 'vallalat', 'letrehozva']

class KonzultansListSerializer(serializers.ModelSerializer):
    szakirany_nev = serializers.CharField(source='szakirany.nev', read_only=True)

    class Meta:
        model = Konzultans
        fields  = [
            'id', 'konzultans_azonosito', 'nev', 'email', 'szakirany', 'szakirany_nev', 'munka_kezdes', 'munka_befejezes', 'aktiv' 
        ]

class IdopontokSerializer(serializers.ModelSerializer):
    konzultans_nev = serializers.CharField(source='konzultans.nev', read_only=True)
    kliens_nev = serializers.CharField(source='kliens.nev', read_only=True)
    szakiran_nev = serializers.CharField(source='szakirany.nev', read_only=True)

    class Meta:
        model = Idopontok
        fields = [
            'id', 'idopont_azonosito', 'kliens', 'kliens_nev', 'konzultans', 'konzultans_nev', 'szakirany', 'szakirany_nev', 'kezdes', 'vege', 'statusz', 'letrehozva'
        ]

class IdopontLetrehozasSerializer(serializers.ModelSerializer):
    """Foglaláskor a kliens adatait közvetlenül elfogadó serializer."""
    kliens_email = serializers.EmailField(write_only=True)
    kliens_nev = serializers.CharField(write_only=True)
    kliens_telefon = serializers.CharField(write_only=True, required=False, allow_blank=True)
    kliens_vallalat = serializers.CharField(write_only=True, required=False, allow_blank=True)
    class Meta:
        model = Idopontok
        fields = [
            'idopont_azonosito', 'konzultans', 'szakirany',
            'kezdes', 'vege', 'statusz',
            'kliens_email', 'kliens_nev', 'kliens_telefon', 'kliens_vallalat'
        ]
        read_only_fields = ['idopont_azonosito', 'statusz']

    def validate(self, data):
        kezdes = data.get('kezdes')
        vege = data.get('vege')
        konzultans= data.get('konzultans')

        if kezdes and vege:
            if kezdes>= vege:
                raise serializers.ValidationError({"vege": "A kezdésnek a vég előtt kell lennie."})

            if kezdes < timezone.now():
                raise serializers.ValidationError({"kezdes": "Múltbéli időpont nem foglalható."})

            #Munkaidő ellenőrzés
            if kezdes.time() < konzultans.munka_kezdes or vege.time() > konzultans.munka_befejezes:
                raise serializers.ValidationError({
                    "kezdes": f"A megadott időpont a konzultáns munkaidején kívül esik ({konzultans.munka_kezdes.strftime('%H:%M')} - {konzultans.munka_befejezes.strftime('%H:%M')})."
                })

        return data

    def create(self, validated_data):
        kliens_email = validated_data.pop('kliens_email')
        kliens_nev = validated_data.pop('kliens_nev')
        kliens_telefon = validated_data.pop('kliens_telefon', '')
        kliens_vallalat = validated_data.pop('kliens_vallalat', '')

        # Meglévő kliens lekérése email alapján, vagy új létrehozása
        kliens, _ = Kliens.objects.get_or_create(
            email=kliens_email,
            defaults={
                'nev': kliens_nev,
                'telefon': kliens_telefon,
                'vallalat': kliens_vallalat
            }
        )

        idopont = Idopontok.objects.create(kliens=kliens, statusz='IGAZOLT', **validated_data)
        return idopont