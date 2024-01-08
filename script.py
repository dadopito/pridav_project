import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd


popular_movies = pd.read_csv('popular_movies.csv')
# print(len(popular_movies))
# first_popular_movies = popular_movies[popular_movies['averageRating'] > 7.9] #done
# second_popular_movies = popular_movies[(popular_movies['averageRating'] <= 7.9) & (popular_movies['averageRating'] > 7.7)] #done
# third_popular_movies = popular_movies[(popular_movies['averageRating'] <= 7.7) & (popular_movies['averageRating'] > 7.5)] #done
# fourth_popular_movies = popular_movies[(popular_movies['averageRating'] <= 7.5) & (popular_movies['averageRating'] > 7.3)] #done
# fifth_popular_movies = popular_movies[popular_movies['averageRating'] <= 7.3] #done

nonpopular_movies = pd.read_csv('nonpopular_movies.csv')
# print(len(nonpopular_movies))
# first_nonpopular_movies = nonpopular_movies[nonpopular_movies['averageRating'] > 5.6] #done
# second_nonpopular_movies = nonpopular_movies[(nonpopular_movies['averageRating'] <= 5.6) & (nonpopular_movies['averageRating'] > 5.4)] #done
# third_nonpopular_movies = nonpopular_movies[(nonpopular_movies['averageRating'] <= 5.4) & (nonpopular_movies['averageRating'] > 5.1)] #done
# fourth_nonpopular_movies = nonpopular_movies[(nonpopular_movies['averageRating'] <= 5.1) & (nonpopular_movies['averageRating'] > 4.6)] #done
# fifth_nonpopular_movies = nonpopular_movies[nonpopular_movies['averageRating'] <= 4.6] #done

def parentalguide_data(id, database):
    url = f'https://www.imdb.com/title/{id}/parentalguide'
    response = requests.get(url)
    content = response.text
    soup = BeautifulSoup(content, 'html.parser')

    sections = ['nudity', 'violence', 'profanity', 'alcohol', 'frightening']
    advisory_info = {section: None for section in sections}

    for section_id in sections:
        section = soup.find('section', {'id': f'advisory-{section_id}'})
        severity_vote_container = section.find('div', {'class': 'advisory-severity-vote__container'}) if section else None
        severity_span = severity_vote_container.find('span') if severity_vote_container else None

        advisory_info[section_id] = severity_span.text.strip() if severity_span else None
    
    database.loc[database['tconst'] == id, 'nudity'] = advisory_info['nudity']
    database.loc[database['tconst'] == id, 'violence'] = advisory_info['violence']
    database.loc[database['tconst'] == id, 'profanity'] = advisory_info['profanity']
    database.loc[database['tconst'] == id, 'alcohol'] = advisory_info['alcohol']
    database.loc[database['tconst'] == id, 'frightening'] = advisory_info['frightening']

def other_data(id, database):
    url = f'https://www.imdb.com/title/{id}/'
    print(url)
    # Nastavenie úrovne logovania ChromeDrivera
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--log-level=3")  # Nastavte úroveň logovania podľa potreby

    driver = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)
    driver.get(url)
    html_content = driver.page_source
    driver.quit()
    soup = BeautifulSoup(html_content, 'html.parser')

    actors = countries = companies = budget = gross_worldwide = None

    #herci
    title_cast_section = soup.find('section', {'data-testid': 'title-cast'})
    if title_cast_section:
        actors_element = title_cast_section.find_all('a', {'data-testid': 'title-cast-item__actor'})
        if actors_element:
            actors = ''
            for i in range(len(actors_element)):
                actors += actors_element[i].text + ', '
            actors = actors[:-2]

    #krajiny povodu a produkcne filmy
    detail_section = soup.find('section', {'data-testid': 'Details'})
    if detail_section:
        countries_element = detail_section.find('li', {'data-testid': 'title-details-origin'})
        countries_text = countries_element.find_all('li', {'class': 'ipc-inline-list__item'}) if countries_element else None
        if countries_element and countries_text:
            countries = ''
            for i in range(len(countries_text)):
                countries += countries_text[i].text + ', '
            countries = countries[:-2]

        companies_element = detail_section.find('li', {'data-testid': 'title-details-companies'})
        companies_text = companies_element.find_all('li', {'class': 'ipc-inline-list__item'}) if companies_element else None
        if companies_element and companies_text:
            companies = ''
            for i in range(len(companies_text)):
                companies += companies_text[i].text + ', '
            companies = companies[:-2]

    #rozpocty
    box_office_section = soup.find('section', {'data-testid': 'BoxOffice'})
    if box_office_section:
        budget_element = box_office_section.find('li', {'data-testid': 'title-boxoffice-budget'})
        budget_text = budget_element.find('span', {'class': 'ipc-metadata-list-item__list-content-item'}).text if budget_element else None
        if budget_text and '(estimated)' in budget_text:
            currency = budget_text[0]
            amount = int(''.join(filter(str.isdigit, budget_text)))
            if currency == '€':
                budget =  amount
            elif currency == '$':
                budget = amount * 0.914
            elif currency == '£':
                budget = amount * 1.16162
            else:
                budget = None

        gross_worldwide_element = box_office_section.find('li', {'data-testid': 'title-boxoffice-cumulativeworldwidegross'})
        gross_worldwide_text = gross_worldwide_element.find('span', {'class': 'ipc-metadata-list-item__list-content-item'}).text if gross_worldwide_element else None
        if gross_worldwide_text:
            currency = gross_worldwide_text[0]
            amount = int(''.join(filter(str.isdigit, gross_worldwide_text)))
            if currency == '€':
                gross_worldwide =  amount
            elif currency == '$':
                gross_worldwide = amount * 0.914
            elif currency == '£':
                gross_worldwide = amount * 1.16162
            else:
                gross_worldwide = None

    database.loc[database['tconst'] == id, 'actors'] = actors
    database.loc[database['tconst'] == id, 'countriesOfOrigin'] = countries
    database.loc[database['tconst'] == id, 'productionCompanies'] = companies
    database.loc[database['tconst'] == id, 'budget'] = budget #estimeted
    database.loc[database['tconst'] == id, 'grossWorldwide'] = gross_worldwide


def add_data(database, name):
    database = database.sort_values(by='averageRating', ascending=False)
    for id in database['tconst'].tolist():
        parentalguide_data(id, database)
        other_data(id, database)
    database.to_csv(f'{name}.csv', index=False)

# add_data(first_popular_movies, 'first_popular_movies') #done
# add_data(second_popular_movies, 'second_popular_movies') #done
# add_data(third_popular_movies, 'third_popular_movies') ##done
# add_data(fourth_popular_movies, 'fourth_popular_movies') #done
# add_data(fifth_popular_movies, 'fifth_popular_movies') #done
    
# add_data(first_nonpopular_movies, 'first_nonpopular_movies') #done
# add_data(second_nonpopular_movies, 'second_nonpopular_movies') #done
# add_data(third_nonpopular_movies, 'third_nonpopular_movies') ##done
# add_data(fourth_nonpopular_movies, 'fourth_nonpopular_movies') #done
# add_data(fifth_nonpopular_movies, 'fifth_nonpopular_movies') #done