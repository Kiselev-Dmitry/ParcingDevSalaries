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
    for page in count(0):
        payload = {
            "professional_role" : 96,
            "area": "1",
            "period": 30,
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
    for page in count(0):
        payload = {
            "town": 4,
            "keyword": "Программист {}".format(language),
            "catalogues": 48,
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
    table_data = [
        (
            "Язык программирования",
            "Найдено вакансий",
            "Обработано вакансий",
            "Средняя зарплата"
        )
    ]
    for language in statistics:
        info = statistics[language]
        table_data.append(
            (
                language,
                info["vacancies_found"],
                info["vacancies_processed"],
                info["average_salary"]
            )
        )
    table_instance = AsciiTable(table_data, title)
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

    languages_datas_hh = {}
    for language in languages:
        vacancies = get_hh_vacancies(language)
        if vacancies:
            languages_datas_hh[language] = get_language_data_hh(vacancies)
    print(return_beautiful_table(languages_datas_hh, "HeadHunter Moscow"))

    languages_datas_sj = {}
    for language in languages:
        vacancies = get_sj_vacancies(language)
        if vacancies:
            languages_datas_sj[language] = get_language_data_sj(vacancies)
    print(return_beautiful_table(languages_datas_sj, "SuperJob Moscow"))
