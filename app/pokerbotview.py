#!/usr/bin/env python3

from telegram import (
    ParseMode,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    Bot,
)
from telegram.utils.promise import Promise
from typing import Tuple
from io import BytesIO

from app.desk import DeskImageGenerator
from app.cards import Cards
from app.entities import (
    Game,
    Player,
    PlayerAction,
    MessageId,
    ChatId,
    Mention,
    Money,
    RateBetRaise,
)


class PokerBotViewer:
    def __init__(self, bot: Bot):
        self._bot = bot
        self._desk_generator = DeskImageGenerator()

    def send_message(self, chat_id: ChatId, text: str) -> Promise:
        return self._bot.send_message(
            chat_id=chat_id,
            parse_mode=ParseMode.MARKDOWN,
            text=text,
        )

    def send_message_reply(
        self,
        chat_id: ChatId,
        message_id: MessageId,
        text: str,
    ) -> Promise:
        return self._bot.send_message(
            reply_to_message_id=message_id,
            chat_id=chat_id,
            parse_mode=ParseMode.MARKDOWN,
            text=text,
        )

    def send_desk_cards_img(
        self,
        chat_id: ChatId,
        cards: Cards,
        caption="",
    ):
        im_cards = self._desk_generator.generate_desk(cards)
        bio = BytesIO()
        bio.name = 'desk.png'
        im_cards.save(bio, 'PNG')
        bio.seek(0)
        return self._bot.send_photo(
            chat_id=chat_id,
            photo=bio,
            caption=caption,
            parse_mode=ParseMode.MARKDOWN,
        )

    @staticmethod
    def _get_cards_markup(cards: Cards) -> ReplyKeyboardMarkup:
        return ReplyKeyboardMarkup(
            keyboard=[cards],
            selective=True,
            resize_keyboard=True,
        )

    @staticmethod
    def _get_turns_markup(change_action: str) -> InlineKeyboardMarkup:
        keyboard = [[
            InlineKeyboardButton(
                text=PlayerAction.fold.value,
                callback_data=PlayerAction.fold.value
            ),
            InlineKeyboardButton(
                text=PlayerAction.all_in.value,
                callback_data=PlayerAction.all_in.value
            ),
            InlineKeyboardButton(
                text=change_action,
                callback_data=change_action
            )
        ]]
        keyboard.append([
            InlineKeyboardButton(
                text=str(RateBetRaise.small.value) + "$",
                callback_data=str(RateBetRaise.small.value)
            ),
            InlineKeyboardButton(
                text=str(RateBetRaise.normal.value) + "$",
                callback_data=str(RateBetRaise.small.value)
            ),
            InlineKeyboardButton(
                text=str(RateBetRaise.big.value) + "$",
                callback_data=str(RateBetRaise.small.value)
            ),
        ])

        return InlineKeyboardMarkup(
            inline_keyboard=keyboard
        )

    def send_cards(
            self,
            chat_id: ChatId,
            cards: Cards,
            mention_markdown: Mention,
    ) -> Promise:
        markup = PokerBotViewer._get_cards_markup(cards)
        return self._bot.send_message(
            chat_id=chat_id,
            text="Showing cards to " + mention_markdown,
            reply_markup=markup,
            parse_mode=ParseMode.MARKDOWN
        )

    @staticmethod
    def define_change_action(
        game: Game,
        player: Player,
    ) -> Tuple[str, str]:
        if player.round_rate == game.max_round_rate:
            return PlayerAction.check.value
        else:
            return PlayerAction.call.value

    def send_turn_actions(
            self,
            chat_id: ChatId,
            game: Game,
            player: Player,
            money: Money,
    ) -> Promise:
        if len(game.cards_table) == 0:
            cards_table = "no cards"
        else:
            cards_table = " ".join(game.cards_table)
        text = (
            "{}, it is your turn\n" +
            "Cards on the table: \n" +
            "{}\n" +
            "Your money: *{}$*\n" +
            "Max round rate: *{}$*"
        ).format(
            player.mention_markdown,
            cards_table,
            money,
            game.max_round_rate,
        )
        change_action = PokerBotViewer.define_change_action(game, player)
        markup = PokerBotViewer._get_turns_markup(change_action)
        return self._bot.send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=markup,
            parse_mode=ParseMode.MARKDOWN
        )

    def remove_markup(
        self,
        chat_id: ChatId,
        message_id: MessageId,
    ) -> Promise:
        return self._bot.edit_message_reply_markup(
            chat_id=chat_id,
            message_id=message_id,
        )
