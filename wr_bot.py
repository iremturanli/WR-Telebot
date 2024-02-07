import requests
from bs4 import BeautifulSoup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

TOKEN = 'YOUR_TOKEN'

def get_champion_about(champion_name):
    url = f"https://www.wildriftfire.com/guide/{champion_name.lower()}"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    lane_options_container = soup.find('div', class_='wf-champion__guide-selector')
    lane_spans = lane_options_container.find_all('span')

    builds = [span.get_text(strip=True) for span in lane_spans if "Build" in span.get_text(strip=True)]

    build_options = "\n".join([f"{i}. {build}" for i, build in enumerate(builds, start=1)])
    return build_options, soup

def start(update, context):
    update.message.reply_text("Hello! To get information about the champion, please enter the name of the champion.")

def champion_info(update, context):
    user_input = update.message.text
    if user_input.isdigit():
        choice = int(user_input)
        if 'BUILD_CHOICE' in context.user_data:
            context.user_data['build_choice'] = choice
            build_choice(update, context)
        else:
            update.message.reply_text("Please enter a champions name.")
    else:
        champion_name = user_input
        build_options, soup = get_champion_about(champion_name)
        if build_options:
            update.message.reply_text(f"Available Builds for {champion_name}:\n{build_options}")
            context.user_data['champion_name'] = champion_name
            context.user_data['BUILD_CHOICE'] = True
            context.user_data['soup'] = soup
        else:
            send_champion_data(update, soup, champion_name)

def send_champion_data(update, soup, champion_name):
    cleaned_items_data_block = clean_text(soup.find('div', class_='wf-champion__data__items data-block').text)
    cleaned_items_data_spells = clean_text(soup.find('div', class_='wf-champion__data__spells data-block').text)
    situational_items_element = soup.find('div', class_='wf-champion__data__situational runes data-block')
    cleaned_items_data_situational_items = "Situational items not available for this champion."
    if situational_items_element:
        cleaned_items_data_situational_items = clean_text(situational_items_element.text)
    recommended_role = get_recommended_role(soup)
    update.message.reply_text(f"{cleaned_items_data_block}")
    update.message.reply_text(f"{cleaned_items_data_spells}")
    update.message.reply_text(f"{cleaned_items_data_situational_items}")
    update.message.reply_text(f"{champion_name}'s Recommended Role: {recommended_role}")

def clean_text(text):
    return '\n\n'.join(line.strip() for line in text.splitlines() if line.strip())

def get_recommended_role(soup):
    champion_role_container = soup.find('div', class_='wf-champion__about__info')
    additional_info = champion_role_container.find('div', class_='additional-info')
    recommended_role_span = additional_info.find('span', class_='title', text='Recommended Role')
    if recommended_role_span:
        recommended_role_data_span = recommended_role_span.find_next_sibling('span', class_='data')
        if recommended_role_data_span:
            return recommended_role_data_span.text.strip()
    return "Role information not available."

def build_choice(update, context):
    choice = context.user_data.get('build_choice')
    champion_name = context.user_data.get('champion_name')
    soup = context.user_data.get('soup')
    selected_classes = {
        1: {'items': 'wf-champion__data__items data-block', 'spells': 'wf-champion__data__spells data-block', 'situational': 'wf-champion__data__situational runes data-block'},
        2: {'items': 'wf-champion__data__items data-block inactive', 'spells': 'wf-champion__data__spells data-block inactive', 'situational': 'wf-champion__data__situational runes data-block inactive'}
    }

    selected_lane_class = selected_classes[choice]['items']
    selected_spells_class = selected_classes[choice]['spells']
    selected_situational_class = selected_classes[choice]['situational']

    cleaned_items_data_block = clean_text(soup.find('div', class_=selected_lane_class).text)
    cleaned_items_data_spells = clean_text(soup.find('div', class_=selected_spells_class).text)
    situational_items_element = soup.find('div', class_=selected_situational_class)
    cleaned_items_data_situational_items = "Situational items not available for this champion."
    if situational_items_element:
        cleaned_items_data_situational_items = clean_text(situational_items_element.text)
    recommended_role = get_recommended_role(soup)
    
    update.message.reply_text(f"{cleaned_items_data_block}")
    update.message.reply_text(f"{cleaned_items_data_spells}")
    update.message.reply_text(f"{cleaned_items_data_situational_items}")
    update.message.reply_text(f"{champion_name}'s Recommended Role: {recommended_role}")


def main():
    updater = Updater(token=TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, champion_info))
    dispatcher.add_handler(MessageHandler(Filters.regex(r'^[1-2]$'), build_choice))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
