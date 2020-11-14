import requests
import schedule

from time import sleep
from datetime import datetime
from bs4 import BeautifulSoup
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from playsound import playsound
from pystray import  Icon, MenuItem as item
from PIL import Image

engine = create_engine('sqlite:///database.db')
Session = sessionmaker(bind=engine)
session = Session()
URL = "https://www.poundsterlinglive.com/data/currencies/usd-pairs/USDRUB-exchange-rate/"
EXIT = False

Base = declarative_base()
class DollarRate(Base):
    __tablename__ = "dollar_rates"
    id = Column(Integer, primary_key=True)
    rate = Column(String, nullable=False)
    dt = Column(DateTime, default=datetime.now())


def get_rate():
    responce = requests.get(URL)
    soup = BeautifulSoup(responce.content, "html.parser")
    table = soup.find('table', {'class': 'table data_stat_table'})
    rate = table.find('b', text="Latest USD/RUB Exchange Rate:").find_next().text.strip()
    return rate


def main(icon):
    cur_rate = get_rate()
    dollar_rate = DollarRate(rate=cur_rate)

    try:
        prev_rate = session.query(DollarRate).order_by(DollarRate.id.desc()).first().rate
    except AttributeError:
        prev_rate = cur_rate

    session.add(dollar_rate)
    session.commit()

    ch = float(cur_rate) - float(prev_rate)
    change = (lambda x: ('+' if x > 0 else '') + str(x))(ch)
    icon.notify(f"{cur_rate} ({change[:6]})")
    playsound('coin.wav')


def loop(icon):
    main(icon)
    global EXIT
    schedule.every(2).hours.do(main)
    while True:
        if EXIT:
            break
        schedule.run_pending()
        sleep(1)


def exit(icon):
    global EXIT
    EXIT = True
    icon.stop()


if __name__ == "__main__":
    menu = (item('Update', main), item('Quit', exit))
    icon = Icon('Icon', Image.open("dollar.ico"), 'Current Rate', menu=menu)
    icon.visible = True
    icon.run(setup=loop)

# pyinstaller.exe -F --onefile --add-data="dollar.ico;." --add-data="coin.wav;." --add-data="database.db;." --paths="X:\src\DollarRateTray\venv\Lib\site-packages" --noconsole DollarRateTray.py