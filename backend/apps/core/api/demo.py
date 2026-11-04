"""API local de importación, generación y publicación; sin elevación de roles."""
import csv
import io
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied, ValidationError, NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.models import Alumno, EjecucionAsignacion, Grupo, Nodo, PlanEstudios, SolicitudMateria
from apps.core.services.identidad import resolver_identidad, obtener_alumno
from apps.core.services.importacion_csv import importar
from apps.core.services.asignacion import generar, publicar, serializar_ejecucion, serializar_resultado
from apps.core.services.errors import ReglaDeNegocioError
from .serializers import ProblemDetailsSerializer


class CsvErrorSerializer(serializers.Serializer):
    archivo=serializers.CharField()
    fila=serializers.IntegerField()
    campo=serializers.CharField()
    mensaje=serializers.CharField()


class ImportRequestSerializer(serializers.Serializer):
    archivos=serializers.DictField(child=serializers.CharField())


class ImportReportSerializer(serializers.Serializer):
    valido=serializers.BooleanField()
    filas=serializers.DictField(child=serializers.IntegerField())
    errores=CsvErrorSerializer(many=True)
    importado=serializers.BooleanField(required=False)


class GrupoOutputSerializer(serializers.Serializer):
    id=serializers.IntegerField()
    materia=serializers.IntegerField()
    clave=serializers.CharField()
    profesor=serializers.CharField()
    cupo=serializers.IntegerField()
    horarios=serializers.JSONField()


class StatsOutputSerializer(serializers.Serializer):
    alumnos=serializers.IntegerField()
    planes=serializers.IntegerField()
    materias=serializers.IntegerField()
    grupos=serializers.IntegerField()
    solicitudes=serializers.IntegerField()
    ejecuciones=serializers.IntegerField()
    publicacion_id=serializers.IntegerField(allow_null=True)


class EjecucionOutputSerializer(serializers.Serializer):
    id=serializers.IntegerField()
    estado=serializers.CharField()
    resumen=serializers.JSONField()
    politica=serializers.JSONField()
    created_at=serializers.DateTimeField()


class ResultadoOutputSerializer(serializers.Serializer):
    alumno=serializers.IntegerField()
    matricula=serializers.CharField(allow_null=True)
    materia=serializers.IntegerField()
    clave_materia=serializers.CharField()
    grupo=serializers.IntegerField(allow_null=True)
    estado=serializers.CharField()
    motivo=serializers.CharField(allow_blank=True)
    detalle=serializers.JSONField()


class EjecucionDetalleSerializer(EjecucionOutputSerializer):
    resultados=ResultadoOutputSerializer(many=True)


class HorarioOutputSerializer(serializers.Serializer):
    ejecucion=serializers.IntegerField()
    resultados=ResultadoOutputSerializer(many=True)


class EmptyRequestSerializer(serializers.Serializer):
    pass


@extend_schema(parameters=[OpenApiParameter('X-Tenant-ID',str,OpenApiParameter.HEADER,
    description='Escuela solicitada; siempre se verifica membresía. Obligatorio con varias membresías.')])
class DemoAdminView(APIView):
    permission_classes=[IsAuthenticated]

    def initial(self,request,*args,**kwargs):
        super().initial(request,*args,**kwargs)
        self.identidad=resolver_identidad(request)
        if not self.identidad.membresia.es_administrador:
            raise PermissionDenied('Se requiere administración escolar.')

    def run(self,pk):
        return get_object_or_404(EjecucionAsignacion,pk=pk,tenant=self.identidad.tenant)

    def finalize_response(self,request,response,*args,**kwargs):
        response=super().finalize_response(request,response,*args,**kwargs)
        response['Cache-Control']='no-store'
        return response


class ImportacionView(DemoAdminView):
    @extend_schema(request=ImportRequestSerializer, responses={200:ImportReportSerializer, (400,'application/problem+json'):ProblemDetailsSerializer})
    def post(self,request,accion):
        if not isinstance(request.data,dict) or set(request.data)!={'archivos'}:
            raise ValidationError({'archivos':'Se requiere únicamente el objeto archivos.'})
        return Response(importar(self.identidad.tenant,request.data['archivos'],confirmar=accion=='confirmar'))


class GruposView(DemoAdminView):
    @extend_schema(responses=GrupoOutputSerializer(many=True))
    def get(self,request):
        groups=Grupo.objects.filter(tenant=self.identidad.tenant).order_by('nodo_id','clave','pk')
        return Response([{'id':g.pk,'materia':g.nodo_id,'clave':g.clave,'profesor':g.profesor,'cupo':g.cupo,'horarios':g.horarios} for g in groups])


class EstadisticasView(DemoAdminView):
    @extend_schema(responses=StatsOutputSerializer)
    def get(self,request):
        tenant=self.identidad.tenant
        run=EjecucionAsignacion.objects.filter(tenant=tenant,estado='PUBLICADO').first()
        return Response({'alumnos':Alumno.objects.filter(tenant=tenant).count(),'planes':PlanEstudios.objects.filter(tenant=tenant).count(),
            'materias':Nodo.objects.filter(tenant=tenant).count(),'grupos':Grupo.objects.filter(tenant=tenant).count(),
            'solicitudes':SolicitudMateria.objects.filter(tenant=tenant).count(),'ejecuciones':EjecucionAsignacion.objects.filter(tenant=tenant).count(),
            'publicacion_id':run.pk if run else None})


class GenerarView(DemoAdminView):
    @extend_schema(request=EmptyRequestSerializer,responses={201:EjecucionOutputSerializer})
    def post(self,request):
        if not isinstance(request.data,dict) or request.data: raise ValidationError({'body':'Esta operación recibe un objeto vacío.'})
        try: run=generar(self.identidad.tenant)
        except ReglaDeNegocioError as exc: raise ValidationError({'detail':str(exc)})
        return Response(serializar_ejecucion(run),status=201)


class EjecucionesView(DemoAdminView):
    @extend_schema(operation_id='demo_asignaciones_listar',responses=EjecucionOutputSerializer(many=True))
    def get(self,request):
        return Response([serializar_ejecucion(r) for r in EjecucionAsignacion.objects.filter(tenant=self.identidad.tenant).order_by('-pk')])


class ResultadoView(DemoAdminView):
    @extend_schema(operation_id='demo_asignaciones_detalle',responses=EjecucionDetalleSerializer)
    def get(self,request,pk):
        run=self.run(pk); data=serializar_ejecucion(run)
        data['resultados']=[serializar_resultado(r) for r in run.resultados.order_by('alumno_id','nodo_id')]
        return Response(data)


class PublicarView(DemoAdminView):
    @extend_schema(request=EmptyRequestSerializer,responses=EjecucionOutputSerializer)
    def post(self,request,pk):
        if not isinstance(request.data,dict) or request.data: raise ValidationError({'body':'Esta operación recibe un objeto vacío.'})
        try: run=publicar(self.run(pk))
        except ReglaDeNegocioError as exc: raise ValidationError({'detail':str(exc)})
        return Response(serializar_ejecucion(run))


def celda_segura(value):
    value=str(value or '')
    return "'"+value if value.lstrip().startswith(('=','+','-','@')) else value


class CsvResultadosView(DemoAdminView):
    @extend_schema(responses={(200,'text/csv'):OpenApiTypes.STR})
    def get(self,request,pk):
        run=self.run(pk); output=io.StringIO(); writer=csv.writer(output)
        writer.writerow(['matricula','materia','grupo','estado','motivo','profesor','horarios'])
        for row in run.resultados.order_by('alumno_id','nodo_id'):
            d=row.detalle
            hours=';'.join(f"{h['dia']}:{h['inicio']//60:02d}:{h['inicio']%60:02d}-{h['fin']//60:02d}:{h['fin']%60:02d}" for h in d['horarios'])
            writer.writerow([celda_segura(x) for x in (d['matricula'],d['clave_materia'],d['grupo'],row.estado,row.motivo,d['profesor'],hours)])
        response=HttpResponse(output.getvalue(),content_type='text/csv; charset=utf-8')
        response['Content-Disposition']=f'attachment; filename="asignaciones-{run.pk}.csv"'
        return response


class HorarioView(APIView):
    permission_classes=[IsAuthenticated]

    @extend_schema(responses=HorarioOutputSerializer,parameters=[OpenApiParameter('X-Tenant-ID',str,OpenApiParameter.HEADER)])
    def get(self,request):
        identidad=resolver_identidad(request); alumno=obtener_alumno(identidad)
        run=EjecucionAsignacion.objects.filter(tenant=identidad.tenant,estado='PUBLICADO').first()
        if run is None: raise NotFound('Todavía no hay resultados publicados.')
        response=Response({'ejecucion':run.pk,'resultados':[serializar_resultado(r) for r in run.resultados.filter(alumno=alumno).order_by('nodo_id')]})
        response['Cache-Control']='no-store'
        return response
