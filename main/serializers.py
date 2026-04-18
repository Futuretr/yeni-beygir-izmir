from rest_framework.serializers import ModelSerializer, Serializer
from rest_framework.utils.serializer_helpers import ReturnDict
from .models import Result


class ResultSerializer(ModelSerializer):
    class Meta:
        model = Result
        fields = '__all__'
    
    def to_representation(self, instance):
        """Remove empty fields from JSON output"""
        data = super().to_representation(instance)
        
        # Remove fields that are None or empty string
        # finish_position should only appear in Result pages (not Fixture)
        # kgs, s20 should only appear in Fixture pages (not Result)
        # time, fark should only appear in Result pages (not Fixture)
        fields_to_remove_if_empty = ['finish_position', 'kgs', 's20', 'last_6_races', 'time', 'fark']
        
        for field in fields_to_remove_if_empty:
            if field in data and (data[field] is None or data[field] == ''):
                del data[field]
        
        return data
