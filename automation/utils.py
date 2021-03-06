import requests
import pandas as pd
from email.message import EmailMessage
import smtplib
import sqlite3
from sqlite3 import Error
from datetime import datetime


def create_connection(url):
    """
    Create a database connection to the SQLite database specified by url.
    """
    conn = None
    try:
        conn = sqlite3.connect(url)
        return conn
    except Error as e:
        print(e)
    return conn


def get_vaccine_availability_data(date, districts, api_url):
    df = pd.DataFrame()  # Empty DataFrame
    for district_number in districts.values():
        api_parameters = {"district_id": district_number, "date": date}
        requested_data = requests.get(
            api_url, params=api_parameters, headers={"Cache-Control": "no-cache"}
        ).json()
        df_temp = pd.DataFrame.from_dict(requested_data["centers"])
        df = df.append(df_temp, ignore_index=True)  # append to the df
    df_final = pd.DataFrame()
    for i in range(len(df)):
        df_test_temp = df.iloc[[i]]
        center_id = df_test_temp["center_id"].iloc[0]
        df_session_temp = pd.DataFrame(df_test_temp["sessions"].explode().tolist())
        df_session_temp["center_id"] = center_id
        df_test_temp = df_test_temp.merge(df_session_temp, how="inner", on="center_id")
        df_final = df_final.append(df_test_temp, ignore_index=True)
    df_final = df_final.drop(columns=["sessions", "vaccine_fees", "slots"])
    return df_final


def is_vaccine_available_18(df):
    """
    Return True if vaccine is available for 18 plus else return False.
    """
    if df.empty:
        return False

    df_available = df[(df["available_capacity"] > 0) & (df["min_age_limit"] == 18)]
    return not df_available.empty


def is_vaccine_available_45(df):
    """
    Return True if vaccine is available for 45 plus else return False.
    """
    if df.empty:
        return False

    df_available = df[(df["available_capacity"] > 0) & (df["min_age_limit"] == 45)]
    return not df_available.empty


def get_email_content_18(df):
    html_string_18 = ""

    if df.empty:
        return html_string_18

    df_available_18 = df[(df["available_capacity"] > 0) & (df["min_age_limit"] == 18)]

    if not df_available_18.empty:
        html_string_18 += """<p align="center"><b><i> 18 - 45 age group</i></b></p>
                        <br>
                        <br>"""

        for index, row in df_available_18.iterrows():
            html_string_18 += f"""
                <p>{row['available_capacity']} {row['vaccine']} are available at {row['name']}
                in {row['district_name']} for {row['min_age_limit']} and above years old.
                </p>
                <br>
                <br>"""

    return html_string_18


def get_email_content_45(df):

    html_string_45 = ""

    if df.empty:
        return html_string_45

    df_available_45 = df[(df["available_capacity"] > 0) & (df["min_age_limit"] == 45)]

    if not df_available_45.empty:

        html_string_45 += """<p align="center"><b><i> 45+ age group</i></b></p>
                        <br>
                        <br>"""

        for index, row in df_available_45.iterrows():
            html_string_45 += f"""
                <p>{row['available_capacity']} {row['vaccine']} are available at {row['name']}
                in {row['district_name']} for {row['min_age_limit']} and above years old.
                </p>
                <br>
                <br>"""

    return html_string_45


def send_email(from_email, to_email, subject, content, credentials, smtp_host):
    """
    Send email containing given content to the given addresses from the given 
    address
    """
    msg = EmailMessage()
    msg["From"] = from_email
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.set_content(content, subtype="html")

    user_name = credentials["user_name"]
    password = credentials["password"]

    with smtplib.SMTP(smtp_host, port=587) as smtp_server:
        smtp_server.ehlo()
        smtp_server.starttls()
        smtp_server.login(user_name, password)
        response = smtp_server.send_message(msg)
        return "Notification sent" if str(type(response)) == "<class 'dict'>" else "Failed to Send mail"


def get_data_for_daily_statistics_table(df):

    df_daily_statistics_data = (
        df.groupby(["district_name", "min_age_limit", "vaccine"])["available_capacity"]
        .sum()
        .reset_index()
    )
    df_daily_statistics_data["vaccine"] = df_daily_statistics_data[
        "vaccine"
    ].str.upper()
    df_daily_statistics_data["timestamp"] = datetime.utcnow().strftime(
        "%Y-%m-%d %H:%M:%S"
    )
    return df_daily_statistics_data


def insert_data_to_daily_statistics_table(df, conn):
    """
    Insert data to the daily_statistics table in the database.
    """
    c = conn.cursor()
    for index, row in df.iterrows():
        try:
            insert_sql_statement = f"""
            INSERT INTO daily_statistics
            (
                district_name,
                min_age_limit,
                vaccine,
                available_capacity,
                timestamp
                )
            VALUES(
                '{row["district_name"]}',
                {row["min_age_limit"]},
                '{row["vaccine"]}',
                '{row["available_capacity"]}',
                '{row["timestamp"]}'
                )
            """
            c.execute(insert_sql_statement)
            conn.commit()
        except Error as e:
            conn.rollback()
            print(e)
