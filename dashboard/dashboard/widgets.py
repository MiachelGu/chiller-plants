from dashing.widgets import NumberWidget

users = 10


class MyWidget(NumberWidget):
    title = "Not a random number"

    def get_value(self):
        global users
        users += 1
        return users

    def get_detail(self):
        global users
        return "Hello user {}".format(users)

    def get_more_info(self):
        global users
        return "Hello user {}, there isn't more info".format(users)
