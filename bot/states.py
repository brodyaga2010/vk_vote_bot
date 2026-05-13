from vkbottle import BaseStateGroup


class VotingStates(BaseStateGroup):
    WAITING_ROW = "waiting_row"
    WAITING_SEAT = "waiting_seat"
    WAITING_CONFIRMATION = "waiting_confirmation"
    WAITING_PARTICIPANT = "waiting_participant"
