import discord
from discord import app_commands
import requests
from datetime import datetime
import matplotlib.pyplot as plt
from io import BytesIO

DISCORD_TOKEN = 'YOUR_DISCORD_TOKEN'
WEATHER_API_KEY = 'YOUR_WEATHER_API_KEY'

class MyClient(discord.Client):
    def __init__(self, intents):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        await self.tree.sync()  # Synchronisiere die Befehle global

    async def on_ready(self):
        print(f'Bot ist eingeloggt als {self.user}.')

intents = discord.Intents.default()
intents.message_content = True
client = MyClient(intents=intents)

@client.tree.command(name="forecast", description="Erhalte die tägliche Wettervorhersage für die nächsten 5 Tage")
@app_commands.describe(city="Die Stadt, für die du die Wettervorhersage wissen möchtest")
async def forecast(interaction: discord.Interaction, city: str):
    try:
        # Versuche, eine erste Antwort zu senden, um den Benutzer zu informieren, dass die Anfrage bearbeitet wird
        await interaction.response.send_message("Bitte warte einen Moment, während die Wettervorhersage abgerufen wird...", ephemeral=True)
        
        print(f"Abfrage für Stadt: {city}")
        forecast_data = get_forecast(city)
        
        if forecast_data:
            days = {}
            for forecast in forecast_data['list']:
                date_str = forecast['dt_txt'].split(" ")[0]
                date = datetime.strptime(date_str, '%Y-%m-%d').strftime('%d.%m.%Y')
                if date not in days:
                    days[date] = {
                        'temps': [],
                        'descriptions': [],
                        'winds': [],
                        'humidities': []
                    }
                days[date]['temps'].append(forecast['main']['temp'])
                days[date]['descriptions'].append(forecast['weather'][0]['description'])
                days[date]['winds'].append(forecast['wind']['speed'])
                days[date]['humidities'].append(forecast['main']['humidity'])

            response = f"Wettervorhersage für {city}:\n"
            dates = []
            avg_temps = []
            avg_winds = []
            avg_humidities = []
            for date, data in sorted(days.items()):
                avg_temp = sum(data['temps']) / len(data['temps'])
                avg_wind = sum(data['winds']) / len(data['winds'])
                avg_humidity = sum(data['humidities']) / len(data['humidities'])
                most_common_description = max(set(data['descriptions']), key=data['descriptions'].count)
                
                response += (f"\n**{date}**\n"
                             f"Durchschnittstemperatur: {avg_temp:.1f}°C\n"
                             f"Wetter: {most_common_description}\n"
                             f"Durchschnittliche Windgeschwindigkeit: {avg_wind:.1f} m/s\n"
                             f"Durchschnittliche Luftfeuchtigkeit: {avg_humidity:.1f}%\n")

                dates.append(date)
                avg_temps.append(avg_temp)
                avg_winds.append(avg_wind)
                avg_humidities.append(avg_humidity)

            # Diagramm erstellen
            fig, ax1 = plt.subplots(figsize=(10, 6))

            ax1.set_xlabel('Datum')
            ax1.set_ylabel('Temperatur (°C)', color='tab:red')
            ax1.plot(dates, avg_temps, 'o-', color='tab:red', label='Durchschnittstemperatur')
            ax1.tick_params(axis='y', labelcolor='tab:red')

            ax2 = ax1.twinx()  # Erstellen einer zweiten Y-Achse
            ax2.set_ylabel('Windgeschwindigkeit (m/s) / Luftfeuchtigkeit (%)')
            ax2.plot(dates, avg_winds, 's-', color='tab:blue', label='Durchschnittliche Windgeschwindigkeit')
            ax2.plot(dates, avg_humidities, '^-', color='tab:green', label='Durchschnittliche Luftfeuchtigkeit')
            ax2.tick_params(axis='y')

            # Legende hinzufügen
            ax1.legend(loc='upper left')
            ax2.legend(loc='upper right')

            fig.tight_layout()  # Vermeide Überlappungen

            # Speichern des Diagramms in einen BytesIO-Stream
            buf = BytesIO()
            plt.savefig(buf, format='png')
            buf.seek(0)
            plt.close(fig)

            # Erstelle ein Bild-Objekt und sende es zusammen mit der Nachricht
            image = discord.File(fp=buf, filename="forecast.png")
            await interaction.followup.send(response, file=image)
        else:
            await interaction.followup.send("Stadt nicht gefunden oder Fehler bei der Abfrage der Wetterdaten.")
    except Exception as e:
        # Fehlerbehandlung: sende eine Fehlermeldung an den Benutzer
        print(f"Fehler: {e}")
        await interaction.followup.send("Ein Fehler ist aufgetreten. Bitte versuche es später erneut.")

def get_weather(city):
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric&lang=de"
    print(f"Abfrage-URL: {url}")
    response = requests.get(url)
    print(f"HTTP-Statuscode: {response.status_code}")
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Fehler bei der Abfrage der Wetterdaten: {response.status_code}")
        return None

def get_forecast(city):
    url = f"http://api.openweathermap.org/data/2.5/forecast?q={city}&appid={WEATHER_API_KEY}&units=metric&lang=de"
    print(f"Abfrage-URL: {url}")
    response = requests.get(url)
    print(f"HTTP-Statuscode: {response.status_code}")
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Fehler bei der Abfrage der Wettervorhersage: {response.status_code}")
        return None

client.run(DISCORD_TOKEN)