from django.db import models
from main.util.collections import OrderedClassMembers
from .exception import MissingData


class Result(models.Model):
    class Meta:
        managed = False
        unique_together = ('race_id', 'horse_id')
    __metaclass__ = OrderedClassMembers

    race_id = models.IntegerField(default=0, primary_key=True)
    race_date = models.DateTimeField(blank=True, null=True)
    race_number = models.IntegerField(default=1)  # Which race of the day (1st, 2nd, 3rd, etc.)
    finish_position = models.CharField(max_length=10, default='')  # Horse's finish position (1, 2, 3, etc.) - only for results
    race_category = models.CharField(max_length=200, default='')  # e.g., "Maiden/DHÖW"
    age_group = models.CharField(max_length=200, default='')  # e.g., "4 Yaşlı Araplar"
    # Prize money (İkramiye)
    prize_1 = models.CharField(max_length=50, default='')
    prize_2 = models.CharField(max_length=50, default='')
    prize_3 = models.CharField(max_length=50, default='')
    prize_4 = models.CharField(max_length=50, default='')
    prize_5 = models.CharField(max_length=50, default='')
    horse_id = models.IntegerField(unique=True)
    jockey_id = models.IntegerField()
    owner_id = models.IntegerField()
    trainer_id = models.IntegerField()
    horse_weight = models.CharField(max_length=200)
    track_type = models.CharField(max_length=200)
    distance = models.IntegerField()
    city = models.CharField(max_length=200)
    horse_name = models.CharField(max_length=200)
    horse_age = models.CharField(max_length=200)
    horse_equipment = models.CharField(max_length=100, default='')  # Takılar (K, DB, etc.)
    horse_father_id = models.IntegerField(default=-1)
    horse_mother_id = models.IntegerField(default=-1)
    # Add name fields for human-readable data
    jockey_name = models.CharField(max_length=200, default='')
    owner_name = models.CharField(max_length=200, default='')
    trainer_name = models.CharField(max_length=200, default='')
    horse_father_name = models.CharField(max_length=200, default='')
    horse_mother_name = models.CharField(max_length=200, default='')
    # Additional racing statistics
    start_no = models.CharField(max_length=50, default='')  # StartId - Kapı numarası
    handicap_weight = models.CharField(max_length=50, default='')  # Hc - Handikap ağırlığı
    last_6_races = models.CharField(max_length=100, default='')  # Son6Yaris - Son 6 yarış
    kgs = models.CharField(max_length=50, default='')  # KGS - Koşu istatistikleri
    s20 = models.CharField(max_length=50, default='')  # s20 - Son 20 koşu
    ganyan = models.CharField(max_length=50, default='')  # Gny - Ganyan
    agf = models.CharField(max_length=50, default='')  # AGFORAN - AGF oranı
    time = models.CharField(max_length=50, default='')  # Derece - Yarış süresi (1.33.07)
    fark = models.CharField(max_length=50, default='')  # Fark - İlk ata fark (2 Boy)

    def get_pure_dict(self, *remove_keys):
        # We need to have a separate dictionary because we are going to pop keys and we need to avoid changing the
        # original object
        ignore_keys = ['_state', 'html_row'] + list(remove_keys)

        filtered_dict = dict((k, v) for k, v in self.__dict__.items() if k not in ignore_keys)

        return filtered_dict

    def __str__(self):
        return "|".join(k + ': ' + repr(str(v)) for k, v in self.get_pure_dict('id').items())

    @property
    def time_as_seconds(self):
        """
            Returns the time string obtanied from the TJK web site to seconds, since split-secods are involved for
            this use case, our seconds are going to be floats
        :return:
        """
        # 1.30.54 or 59.32

        # 100 split-second = 1 second
        # 1 minute = 60 seconds
        units_as_seconds = [0.01, 1, 60]

        # Split by the dot
        split = self.time.split('.')

        if self.time == "Derecesiz":
            raise MissingData('Horse either did not finish the race, or had not run in the first place!')

        # Reverse the array to start from the split-second since minutes might not be there
        reversed_time = split[::-1]

        total_seconds = 0
        # Multiply the value by corresponding unit value and add it to total_seconds
        for i, t in enumerate(reversed_time):
            total_seconds += int(t) * units_as_seconds[i]
        return round(total_seconds, 2)
