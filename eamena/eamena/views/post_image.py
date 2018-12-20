import os
import json
import uuid
from datetime import datetime
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from arches.app.models.resource import Resource
from arches.app.utils.imageutils import generate_thumbnail

@csrf_exempt
def create_inf_resource(request):
    '''this is the view that handles the file upload ajax call. it includes a
    very simple test for the file format, which should be XLSX, and returns the
    file path, name, and validity, all of which are used on the front-end.'''

    if request.method == 'POST':

        ## collect all the data from the request
        f = request.FILES.get('file', None)
        lat = request.POST.get('latitude', '')
        lng = request.POST.get('longitude', '')
        caption = request.POST.get('caption', '')
        time = request.POST.get('captureDate', '')
        
        if f is None:
            return HttpResponse(json.dumps({"error_msg":"incomplete data posted"}),
                content_type="application/json",
                status=500
            )

        ## transform some of the data
        wkt = "POINT ( {} {} )".format(lng, lat)
        yyyymmdd = datetime.fromtimestamp(float(time)).strftime('%Y-%m-%d')

        ## create resource instance
        res = Resource()
        res.entitytypeid = 'INFORMATION_RESOURCE.E73'
        res.set_entity_value('DESCRIPTION.E62', caption)
        res.set_entity_value('DATE_OF_ACQUISITION.E50', yyyymmdd)
        res.set_entity_value('SPATIAL_COORDINATES_GEOMETRY.E47', wkt)
        res.set_entity_value('FILE_PATH.E62', f)
        thumb = generate_thumbnail(f)
        if thumb != None:
            res.set_entity_value('THUMBNAIL.E62', thumb)
        res.save()
        res.index()

        response = {
            "resourcetypeid":res.entitytypeid,
            "resourceid": res.entityid,
            "filename": f._name,
            "date": yyyymmdd,
            "location": wkt,
            "caption": caption,
        }

        return HttpResponse(json.dumps(response),
            content_type="application/json",
            status=201
        )