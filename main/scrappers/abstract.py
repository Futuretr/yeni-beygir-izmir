from bs4 import BeautifulSoup
import urllib.request
import datetime
import re
from . import logger
from main.exception import PageDoesNotExist
import time
from main.enums import ManagerType, PageType
from main.models import Result
from ..serializers import ResultSerializer


class BaseRaceDayScrapper:
    """
    Race Day Scrapper(RDS) makes a request to an url in order to get the page source that contains information about
    the past, present or upcoming races usually from Turkey.
    """

    """
    Each race day contains many races and each of them wrapped by a single div tag, and it's class is 'races-panes'.
    We store that div inside this property
    """
    race_divs = ''

    """
    Fixture and Result pages have minor differences, therefore they need different scrappers to scrap html table rows
    """
    row_scrapper = ''

    page_type = ''

    url = ''

    rows = list()

    """
        Fixture and Result has one particular difference in the url, thus this property determines that
        Fixture: 'GunlukYarisProgrami'
        Result: 'GunlukYarisSonuclari'
        """
    race_type = ''

    def __init__(self, city, date):
        self.race_day = ''
        self.city = city
        self.date = date

        # Create an empty list to hold each race
        self.races = []

        self.set_url()
        try:
            # Get the html of the page that contains the results
            self.html = urllib.request.urlopen(self.url).read()
        except urllib.request.HTTPError as http_error:
            raise PageDoesNotExist(str(http_error), self.url)

        self.race_divs = self.get_race_divs()

    @classmethod
    def from_date_values(cls, city, year, month, day):
        return cls(city, datetime.date(year, month, day))

    def set_url(self):
        # -- start url parsing --
        # Updated for new TJK.org website structure (2026)
        # {0} is race type, {1} is city id, {2} is date, {3} is city name
        # Remove &Era=today for past dates to access historical program pages
        self.url = 'https://www.tjk.org/TR/YarisSever/Info/Sehir/{0}?SehirId={' \
                   '1}&QueryParameter_Tarih={2}&SehirAdi={3}'

        # Feeding the city information to url
        self.url = self.url.format(self.race_type, self.city.value, '{0}', self.city.name)

        # Feeding the date information to url by formatting the date to appropriate string
        # Ex: '03%2F07%2F2017'
        # But first we use dashes as separator so we won't confuse 'date.strftime' function
        date_format = '{0}-{1}-{2}'.format('%d', '%m', '%Y')

        # Now we are replacing dashes with appropriate chars to match the original url
        formatted_dated = self.date.strftime(date_format).replace('-', '%2F')

        self.url = self.url.format(formatted_dated)
        # -- end url parsing --

        logger.info(self.url)

    def get_race_divs(self):
        # Get the Soap object for easy scraping
        soup = BeautifulSoup(self.html, "lxml")
        # Get the div containing all the races
        race_div = soup.find("div", class_='races-panes')
        # Check if the page is valid
        if not race_div:
            raise PageDoesNotExist('', self.url)

        # Getting the one level inner divs which contains each race. Recursive is set to false because we don't want
        # to go the the inner child of those divs. Just trying to stay on the first level
        return race_div.find_all("div", recursive=False)

    def process(self):
        # Process each race
        logger.info('Processing each race')

        for race_index, rDiv in enumerate(self.race_divs):
            logger.info('{0} race(s) remain'.format(len(self.race_divs) - race_index))

            # Get the raw race details
            race_id = int(rDiv.get('id'))

            race_detail_div = rDiv.find("div", class_="race-details")

            # The race_detail_div contains some needed information on one of it's children <h3>
            race_info_html = race_detail_div.find("h3", class_="race-config")

            # Updated for new TJK.org structure (2026)
            # Get all text and split by comma
            race_text = race_info_html.get_text()
            
            # Parse race info: "Maiden/DHÖW , 4 Yaşlı Araplar, 58 kg, 1200 Kum , E.İ.D. : 120.28"
            race_parts = [part.strip() for part in race_text.split(',')]
            
            race_category = ""
            age_group = ""
            
            if len(race_parts) >= 1:
                race_category = race_parts[0]  # "Maiden/DHÖW"
            if len(race_parts) >= 2:
                age_group = race_parts[1]  # "4 Yaşlı Araplar"
            
            # Extract distance and track type
            distance = "0"
            track_type = "Kum"
            
            # Find all numbers in race_text and get the largest (likely the distance in meters)
            all_numbers = re.findall(r'\d+', race_text)
            if all_numbers:
                # Convert to integers and find the max (distance is usually 1000-3000)
                numbers_as_int = [int(n) for n in all_numbers]
                # Distance is typically between 800 and 4000 meters
                distance_candidates = [n for n in numbers_as_int if 800 <= n <= 4000]
                if distance_candidates:
                    distance = str(max(distance_candidates))
                elif numbers_as_int:
                    # If no number in range, take the largest number
                    distance = str(max(numbers_as_int))
            
            # Extract track type (Kum, Çim, etc.)
            track_keywords = ['Kum', 'Çim', 'Sentetik']
            for keyword in track_keywords:
                if keyword in race_text:
                    track_type = keyword
                    break
            
            # Extract prizes (İkramiye)
            prize_1 = prize_2 = prize_3 = prize_4 = prize_5 = ""
            
            # Get all text from the race div to find prizes
            race_div_text = rDiv.get_text()
            
            # Extract İkramiye (Prize money) - numbers with format like "545.000"
            ikramiye_match = re.search(r'İkramiye[:\s-]+(.+?)(?:Yetiştirici|At Sahibi|$)', race_div_text, re.DOTALL | re.IGNORECASE)
            if ikramiye_match:
                # Find numbers in format 545.000 or 218.000
                prizes = re.findall(r'\d+\.\d+', ikramiye_match.group(1))
                if len(prizes) >= 1: prize_1 = prizes[0]
                if len(prizes) >= 2: prize_2 = prizes[1]
                if len(prizes) >= 3: prize_3 = prizes[2]
                if len(prizes) >= 4: prize_4 = prizes[3]
                if len(prizes) >= 5: prize_5 = prizes[4]

            # Common data for the race is ready, time to get the results get the result of each horse in the table
            rows = rDiv.find("tbody").find_all("tr")

            # Create an empty list to hold each result for this race
            results = []
            # Go through the each result and process
            for i, row in enumerate(rows):
                # Initialize the scrapper for a single row
                scrapper = self.row_scrapper(row)

                # Get the result model with scrapped data in it
                model = scrapper.get()
                
                # Set finish position based on row index (1-based) for results
                if self.page_type == PageType.Result:
                    model.finish_position = str(i + 1)

                # Assign the values that are specific to this race
                model.track_type = track_type
                model.distance = int(distance)
                model.race_id = race_id
                model.race_number = race_index + 1  # 1st race, 2nd race, etc.
                model.race_category = race_category
                model.age_group = age_group
                model.prize_1 = prize_1
                model.prize_2 = prize_2
                model.prize_3 = prize_3
                model.prize_4 = prize_4
                model.prize_5 = prize_5
                model.city = self.city.name
                model.race_date = self.date

                # Append the model to the result list
                results.append(model)
            # This point we have all the results of one race we can append it to the race list
            self.races.append(results)

            self.rows.append(rows)
        # We got all the information about the race day in the given city and date. We can return the races list now
        logger.info('Completed!')

    def serialize(self):
        race_day_dict = {}
        for i, race in enumerate(self.races):
            race_day_dict[i] = ResultSerializer(race, many=True).data
        return race_day_dict

    @classmethod
    def scrap_by_date(cls, city, date):
        """
        Scraps the results of the supplied city and date
        :param city: City which the race happened
        :param date: datetime object for the desired race
        :return: Returns the results of the desired race
        """
        scrapper = cls(city, date)
        scrapper.process()
        return scrapper

    @classmethod
    def scrap(cls, city, year, month, day):
        """
        Scraps the results of the supplied city and date values
        :param city: City which the race happened
        :param year: The year of the wanted race
        :param month: The month of the wanted race
        :param day: The day of the wanted race
        :return: Returns the results of the desired race
        """
        return cls.scrap_by_date(city, datetime.datetime(year, month, day))


class BaseRaceDayRowScrapper:
    """
      Class name used for horses' name in TJK's site, after "gunluk-GunlukYarisProgrami-"
      Ex: <td class="gunluk-GunlukYarisProgrami-AtAdi">
      """
    horse_name_class_name = ''
    page_type = ''

    """
    Beginning of the class name used for each row in the tables, Fixture and Result tables has it differently
    Ex for fixture: <td class="gunluk-GunlukYarisProgrami-AtAdi">
    Ex for result: <td class="gunluk-GunlukYarisSonuclari-AtAdi3">
    """
    td_class_base = ''

    def __init__(self, html_row):
        self.row = html_row

    def get(self):
        model = Result()

        # Get manager IDs and names
        model.jockey_id = self.get_manager_id(ManagerType.Jockey)
        model.jockey_name = self.get_manager_name(ManagerType.Jockey)
        
        model.owner_id = self.get_manager_id(ManagerType.Owner)
        model.owner_name = self.get_manager_name(ManagerType.Owner)
        
        model.trainer_id = self.get_manager_id(ManagerType.Trainer)
        model.trainer_name = self.get_manager_name(ManagerType.Trainer)

        # The third column in the table contains the name of the horse and a link that goes to that horse's page.
        # Also the link will have the id of the horse and the abbreviations that come after the name which tells
        # status information, for example whether the horse will run with an eye patch and etc.
        # More info is here: http://www.tjk.org/TR/YarisSever/Static/Page/Kisaltmalar
        horse_name_html = self.get_column(self.horse_name_class_name).find('a')

        # first element is the name it self, others are the abbreviations, so we get the first and assign it as name
        model.horse_name = str(horse_name_html.contents[0]).strip()
        
        # Extract horse equipment (takılar) - look for span tags with abbreviations (K, DB, etc.)
        horse_name_cell = self.get_column(self.horse_name_class_name)
        equipment_parts = []
        
        # Find all span tags in the cell (they contain abbreviations)
        spans = horse_name_cell.find_all('span')
        for span in spans:
            abbr = span.get_text().strip()
            if abbr and abbr not in ['\n', '']:
                equipment_parts.append(abbr)
        
        # Also check for text nodes after the link
        if not equipment_parts:
            for content in horse_name_html.next_siblings:
                if hasattr(content, 'get_text'):
                    text = content.get_text().strip()
                elif isinstance(content, str):
                    text = content.strip()
                else:
                    continue
                if text and text not in ['<br/>', '<br>', '', '\n']:
                    equipment_parts.append(text)
        
        model.horse_equipment = ' '.join(equipment_parts) if equipment_parts else ''

        # Now get the id of the horse from that url
        model.horse_id = int(self.get_id_from_a(horse_name_html))

        # Get the model of the horse from the fourth column
        model.horse_age = self.get_column_content("Yas")

        # Horses father and mother are combined in a single column in separate <a> So we find all the <a> in the
        # column and only get their id's from respected links. Father is the first, mother is the second
        parent_links = self.get_column("Baba").find_all('a', href=True)

        # Process the father
        model.horse_father_id = int(self.get_id_from_a(parent_links[0]))
        model.horse_father_name = parent_links[0].get_text().strip() if parent_links[0] else ''

        # Process the mother
        model.horse_mother_id = int(self.get_id_from_a(parent_links[1]))
        model.horse_mother_name = parent_links[1].get_text().strip() if len(parent_links) > 1 and parent_links[1] else ''

        # Get the weight of the horse during the time of the race
        # Clean "Fazla Kilo" and extra weight (e.g., "58+0.20Fazla Kilo" -> "58")
        horse_weight_raw = self.get_column_content("Kilo")
        horse_weight_cleaned = re.sub(r'Fazla\s*Kilo', '', horse_weight_raw).strip()
        # Remove +X.XX part (e.g., "54+2.00" -> "54")
        horse_weight_cleaned = re.sub(r'\+[\d.,]+', '', horse_weight_cleaned).strip()
        model.horse_weight = horse_weight_cleaned

        # Get additional racing statistics and clean -1 values
        model.start_no = self.get_column_content("StartId")
        model.handicap_weight = self.get_column_content("Hc")
        
        last_6 = self.get_column_content("Son6Yaris")
        model.last_6_races = '' if not last_6 or last_6 in ['-1', '-'] else last_6
        
        # KGS and s20 are only available in Fixture (program) pages, not in Result pages
        from main.enums import PageType
        if self.page_type == PageType.Fixture:
            # Get KGS (Koşmadığı Gün Sayısı)
            kgs_val = self.get_column_content("KGS")
            model.kgs = '' if not kgs_val or kgs_val in ['-1', '-'] else kgs_val
            
            # Get S20 (Son 20 koşu)
            s20_val = self.get_column_content("S20")
            model.s20 = '' if not s20_val or s20_val in ['-1', '-'] else s20_val
        else:
            # For Result pages, these fields don't exist
            model.kgs = ''
            model.s20 = ''
        
        model.ganyan = self.get_column_content("Gny")
        
        # Clean AGF - extract only first percentage value (e.g., %29 from %29(1)%32(1))
        agf_raw = self.get_column_content("AGFORAN")
        agf_match = re.search(r'%\d+', agf_raw)
        model.agf = agf_match.group(0) if agf_match else agf_raw
        
        # Get Derece (time) and Fark (difference) - only for Result pages
        if self.page_type == PageType.Result:
            model.time = self.get_column_content("Derece")
            model.fark = self.get_column_content("Fark")
        else:
            model.time = ''
            model.fark = ''

        return model

    def get_manager_id(self, _type):
        """
        :param _type: The content of the column where the according type of manager is
        :return: id of the desired manager either Jockey, Owner or Trainer
        """
        try:
            # Sometimes the info is not there, so we have to be safe
            return int(self.get_id_from_a(self.get_column(_type.value).find('a', href=True)))
        except:
            # Info is not there, mark it as missing
            return -1

    def get_manager_name(self, _type):
        """
        :param _type: The content of the column where the according type of manager is
        :return: name of the desired manager either Jockey, Owner or Trainer
        """
        try:
            column = self.get_column(_type.value)
            a_tag = column.find('a', href=True)
            if a_tag:
                return a_tag.get_text().strip()
            return ''
        except:
            return ''

    def get_column(self, col_name):
        """
        :param col_name: The value after the gunluk-GunlukYarisSonuclari-{0}
        :return: The content in the column(td) that has a class name starting with gunluk-GunlukYarisSonuclari-
        """
        return self.row.find("td", class_="{0}{1}".format(self.td_class_base, col_name))

    def get_column_content(self, col_name):
        """
        Striped_strings property returns a collection containing the values. Then ve do a string join to have the
        actual value in the tag. The value might me missing, then we simply return -1 to indicate that it is missing.
        :param col_name: The value after the gunluk-GunlukYarisSonuclari-{0}
        :return: The content in the column(td) that has a class name starting with gunluk-GunlukYarisSonuclari-
        """
        column = self.get_column(col_name)
        return "".join(column.stripped_strings if column else '-1')

    @staticmethod
    def get_id_from_a(a):
        """"
        The url's contain the id, after the phrase Id=
        :param a: The html code of a tag
        :return: id of the supplied a tag
        """
        if a:
            # We split from that and take the rest
            id_ = a['href'].split("Id=")[1]

            # We split one more time in case of there is more after the id
            # We take the first part this time
            id_ = id_.split("&")[0]

            return id_
