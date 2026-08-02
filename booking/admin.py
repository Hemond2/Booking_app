from django.contrib import admin
from .models import SzakmaIrany, Kliens, Konzultans, Idopontok


@admin.register(SzakmaIrany)
class SzakmaiIranyAdmin(admin.ModelAdmin):
    list_display = ("id", "nev", "leiras")

@admin.register(Kliens)
class KliensAdmin(admin.ModelAdmin):
    list_display = ("nev", "vallalat", "email", "telefon")
    search_fields = ("nev", "vallalat", "email", "telefon")

@admin.register(Konzultans)
class KonzultansAdmin(admin.ModelAdmin):
    list_display = ('nev', 'szakirany', 'munka_kezdes', 'munka_befejezes', 'aktiv')
    list_filter = ('szakirany', 'aktiv')
    search_fields = ('nev', 'email')

@admin.register(Idopontok)
class IdopontokAdmin(admin.ModelAdmin):
    list_display = ('konzultans', 'kliens', 'kezdes', 'vege', 'statusz')
    list_filter = ('statusz', 'szakirany')
    search_fields = ('kliens__nev', 'konzultans__nev')
