from datetime import datetime, timedelta
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.generics import ListAPIView
from django.utils.dateparse import parse_date
from django.utils import timezone
from django.db import transaction

from .models import SzakmaIrany, Kliens, Konzultans, Idopontok
from .serializers import (
    SzakmaIranySerializer,
    KonzultansListSerializer,
    IdopontokSerializer, 
    IdopontLetrehozasSerializer
)

class SzakmaIranyListView(ListAPIView):
    """GET /api/szakaranyok/ - Szakterületek listázása"""
    queryset = SzakmaIrany.objects.all()
    serializer_class = SzakmaIranySerializer

class KonzultansListView(ListAPIView):
    """GET /api/konzultansok/?szakirany_id=1 - Konzultánsok szűrése szakterület alapján"""
    serializer_class = KonzultansListSerializer

    def get_queryset(self):
        queryset = Konzultans.objects.filter(aktiv=True)
        szakirany_id = self.request.query_params.get('szakirany_id')
        if szakirany_id:
            queryset = queryset.filter(szakirany_id=szakirany_id)
        return queryset

class KonzultansElerhetosegHoverView(APIView):
    """
    GET /api/konzultansok/<id>/elerhetoseg/?datum=YYYY-MM-DD
    A React UI hover állapothoz tartozó elérhetőség összefoglaló.
    """
    def get(self, request, pk):
        try:
            konzultans = Konzultans.objects.get(pk=pk, aktiv=True)
        except Konzultans.DoesNotExist:
            return Response({"error": "Konzultáns nem található"}, status=status.HTTP_404_NOT_FOUND)

        datum_str = request.query_params.get('datum')
        cel_datum = parse_date(datum_str) if datum_str else timezone.now().date()

        # A modelledben meglévő elerhetoseg_osszegzes metódus meghívása
        osszegzes = konzultans.elerhetoseg_osszegzes(cel_datum=cel_datum)
        return Response(osszegzes, status=status.HTTP_200_OK)

class KonzultansIdosavPickerView(APIView):
    """
    GET /api/konzultansok/<id>/idosavok/?datum=YYYY-MM-DD
    1 órás idősávokat generál a naptár választóhoz.
    """
    def get(self, request, pk):
        try:
            konzultans = Konzultans.objects.get(pk=pk, aktiv=True)
        except Konzultans.DoesNotExist:
            return Response({"error": "Konzultáns nem található"}, status=status.HTTP_404_NOT_FOUND)

        datum_str = request.query_params.get('datum')
        cel_datum = parse_date(datum_str) if datum_str else timezone.now().date()

        nap_kezdet = timezone.make_aware(datetime.combine(cel_datum, konzultans.munka_kezdes))
        nap_vege = timezone.make_aware(datetime.combine(cel_datum, konzultans.munka_befejezes))

        meglevo_foglalasok = Idopontok.objects.filter(
            konzultans=konzultans,
            kezdes__lt=nap_vege,
            vege__gt=nap_kezdet,
            statusz__in=['FÜGGŐ', 'IGAZOLT']
        )

        idosavok = []
        aktualis = nap_kezdet
        while aktualis + timedelta(hours=1) <= nap_vege:
            sav_vege = aktualis + timedelta(hours=1)

            foglalt = meglevo_foglalasok.filter(
                kezdes__lt=sav_vege,
                vege__gt=aktualis
            ).exists()

            idosavok.append({
                "kezdes": aktualis.isoformat(),
                "vege": sav_vege.isoformat(),
                "formazott_ido": f"{aktualis.strftime('%H:%M')} - {sav_vege.strftime('%H:%M')}",
                "szabad": not foglalt
            })
            aktualis += timedelta(hours=1)

        return Response({
            "konzultans_id": konzultans.id,
            "datum": cel_datum.isoformat(),
            "idosavok": idosavok
        }, status=status.HTTP_200_OK)

class IdopontLetrehozasView(APIView):
    """
    POST /api/idopontok/
    Új időpont foglalása tranzakcióbiztos módon.
    """
    def post(self, request):
        serializer = IdopontLetrehozasSerializer(data=request.data)
        if serializer.is_valid():
            try:
                with transaction.atomic():
                    idopont = serializer.save()
                    return Response({
                        "uzenet": "Időpont sikeresen lefoglalva!",
                        "idopont_azonosito": str(idopont.idopont_azonosito),
                        "statusz": idopont.statusz,
                        "kezdes": idopont.kezdes,
                        "vege": idopont.vege
                    }, status=status.HTTP_201_CREATED)
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class KliensIdopontokListView(APIView):
    """GET /api/kliensek/<kliens_azonosito>/idopontok/ - Kliens előzményei"""
    def get(self, request, kliens_azonosito):
        try:
            kliens = Kliens.objects.get(kliens_azonosito=kliens_azonosito)
        except Kliens.DoesNotExist:
            return Response({"error": "Kliens nem található"}, status=status.HTTP_404_NOT_FOUND)

        idopontok = kliens.idopontok.all().order_by('-kezdes')
        serializer = IdopontokSerializer(idopontok, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    