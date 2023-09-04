import requests
import os
from dotenv import load_dotenv
from itertools import count
from terminaltables import AsciiTable


def predict_salary(salary_from, salary_to):
    if salary_from is None:
        predicted_salary = 0.8 * salary_to
    elif salary_to is None:
        predicted_salary = 1.2 * salary_from
    else:
        predicted_salary = 0.5 * (salary_from + salary_to)
    return predicted_salary


def predict_rub_salary_hh(vacancy):
    salary = vacancy["salary"]
    salary_from = salary["from"]
    salary_to = salary["to"]
    currency = salary["currency"]
    if currency == "RUR":
        return predict_salary(salary_from, salary_to)


def predict_rub_salary_sj(vacancy):
    salary_from = vacancy["payment_from"]
    salary_to = vacancy["payment_to"]
    currency = vacancy["currency"]
    if currency == "rub" and (salary_from > 0 or salary_to > 0):
        return predict_salary(salary_from, salary_to)


def get_hh_vacancies(language):
    hh_url = "https://api.hh.ru/vacancies/"
    vacancies = []
    developer_id = 96
    moscow_area = "1"
    publication_period = 30
    for page in count(0):
        payload = {
            "professional_role" : developer_id,
            "area": moscow_area,
            "period": publication_period,
            "text": "Программист {}".format(language),
            "only_with_salary": True,
            "page": page,
            "per_page": 100
        }
        response = requests.get(hh_url, params=payload)
        response.raise_for_status()
        hh_reply = response.json()
        vacancies = vacancies + hh_reply["items"]
        if page >= hh_reply["pages"]:
            break
    return vacancies


def get_language_data_hh(vacancies):
    wrong_currency = 0
    sum_salary = 0
    for index, vacancy in enumerate(vacancies):
        predicted_salary = predict_rub_salary_hh(vacancy)
        if predicted_salary is None:
            wrong_currency += 1
            continue
        sum_salary = sum_salary + predicted_salary
    vacancies_found = index+1
    vacancies_processed = vacancies_found-wrong_currency
    language_avr_salary = int(sum_salary/vacancies_processed)
    return {
        "vacancies_found": vacancies_found,
        "vacancies_processed": vacancies_processed,
        "average_salary": language_avr_salary
    }


def get_sj_vacancies(language):
    load_dotenv()
    super_job_token = os.environ["SUPER_JOB_TOKEN"]
    url = "https://api.superjob.ru/2.0/vacancies/"
    headers = {"X-Api-App-Id": super_job_token}
    vacancies = []
    moscow_id = 4
    developer_id = 48
    for page in count(0):
        payload = {
            "town": moscow_id,
            "keyword": "Программист {}".format(language),
            "catalogues": developer_id,
            "page": page,
            "count": 100,
        }
        response = requests.get(url, headers=headers, params=payload)
        response.raise_for_status()
        sj_reply = response.json()
        vacancies = vacancies + sj_reply["objects"]
        if not sj_reply["more"]:
                break
    return vacancies


def get_language_data_sj(vacancies):
    wrong_currency = 0
    sum_salary = 0
    for index, vacancy in enumerate(vacancies):
        predicted_salary = predict_rub_salary_sj(vacancy)
        if predicted_salary is None:
            wrong_currency += 1
            continue
        sum_salary = sum_salary + predicted_salary
    vacancies_found = index + 1
    vacancies_processed = vacancies_found - wrong_currency
    language_avr_salary = int(sum_salary / vacancies_processed)
    return {
        "vacancies_found": vacancies_found,
        "vacancies_processed": vacancies_processed,
        "average_salary": language_avr_salary
    }


def return_beautiful_table(statistics, title):
    table_header = [
        (
            "Язык программирования",
            "Найдено вакансий",
            "Обработано вакансий",
            "Средняя зарплата"
        )
    ]
    for language in statistics:
        language_statistics = statistics[language]
        table_header.append(
            (
                language,
                language_statistics["vacancies_found"],
                language_statistics["vacancies_processed"],
                language_statistics["average_salary"]
            )
        )
    table_instance = AsciiTable(table_header, title)
    return table_instance.table


if __name__ == "__main__":
    languages = [
        "Python",
        "JavaScript",
        "Java",
        "Ruby",
        "PHP",
        "C++",
        "C#",
        "Go"
    ]

    statistics_per_language_hh = {}
    for language in languages:
        vacancies = get_hh_vacancies(language)
        if vacancies:
            statistics_per_language_hh[language] = get_language_data_hh(vacancies)
    print(return_beautiful_table(statistics_per_language_hh, "HeadHunter Moscow"))

    statistics_per_language_sj = {}
    for language in languages:
        vacancies = get_sj_vacancies(language)
        if vacancies:
            statistics_per_language_sj[language] = get_language_data_sj(vacancies)
    print(return_beautiful_table(statistics_per_language_sj, "SuperJob Moscow"))
