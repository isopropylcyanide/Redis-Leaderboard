import sys
import redis

r = redis.StrictRedis(host='localhost', port=6379, db=0,
                      charset="utf-8", decode_responses=True)


class User:
    """A model user having a name, country, email and a score"""

    def __init__(self, name="Default", country="India", email="default@email.com",  score=0):
        self.name = name
        self.email = email
        self.country = country
        self.score = score

    def __repr__(self):
        return '[' + str(self.name) + ',' + str(self.email) + ',' + str(self.country) + ',' + str(self.score) + ']'


def displayLeaderBoard(users):
    """Modelling a basic leaderboard with fields such as name, email, country and score"""
    print('*'*50)
    for index, user in enumerate(users):
        print('%3r %10r | %10r | %10r | %10r' %
              (index + 1, user.email, user.name, user.country, user.score))
    print('*'*50)


COMMAND_LIST = {
    'UPSERT_USER': {
        'id': 1,
        'args': ['name', 'email', 'country'],
        'optionalArgs': []
    },
    'UPSERT_SCORE': {
        'id': 2,
        'args': ['email', 'score'],
        'optionalArgs': []

    },
    'GET_TOP': {
        'id': 3,
        'args': ['k'],
        'optionalArgs': ['country']
    },
    'GET_USERS_WITH_SCORE': {
        'id': 4,
        'args': ['score'],
        'optionalArgs': []
    },
    'SEARCH': {
        'id': 4,
        'args': [],
        'optionalArgs': ['name', 'score', 'country']
    },
}


class QueryBuilder:
    """A general purpose class """

    def __init__(self):
        pass

    def parse(self, inputParams=[]):
        self.inputParams = inputParams
        self.command = self.inputParams[0]
        self.parseCommand()

    def parseCommand(self):
        if self.command is None or not isinstance(self.command, str) or self.command not in COMMAND_LIST:
            sys.exit('Invalid command specified. It has to be a valid string')

        command = COMMAND_LIST[self.command]
        if len(self.inputParams[1:]) < len(command['args']):
            sys.exit(self.command + ' is missing the required parameters')

        if self.command == 'UPSERT_USER':
            name, country, email = self.inputParams[1:]
            addUser(name, country, email)

        elif self.command == 'UPSERT_SCORE':
            email = self.inputParams[1]
            newScore = self.inputParams[2]
            upsertScore(email, newScore)

        elif self.command == 'GET_USERS_WITH_SCORE':
            score = self.inputParams[1]
            getUsersWithScore(score)

        elif self.command == 'GET_TOP':
            k = int(self.inputParams[1])
            try:
                country = self.inputParams[2]
            except IndexError:
                country = None
            getTopHighest(k, country)

        elif self.command == 'SEARCH':
            try:
                name = self.inputParams[2]
            except IndentationError as e:
                name = None
            try:
                score = self.inputParams[3]
            except IndentationError as e:
                score = None
            try:
                country = self.inputParams[4]
            except IndentationError as e:
                country = None
            search(name, score, country)


def addUser(name, country, email, score=0, display=True):
    """Adds user properties by email hash to hmset and upsert score with 0"""
    hashKey = 'user_' + email
    if r.exists(hashKey):
        print('User ' + email + ' is already present. ')
    else:
        mapping = {
            'name': name,
            'country': country
        }
        r.hmset(hashKey, mapping)
        upsertScore(email, score)
        print('User ' + email + ' added to leaderboard with a score of %s. ' % (score))
        createLeaderboard(leaders=None, display=display)


def search(name, score, country):
    pass


def upsertScore(email, score):
    """Upsert score in a sorted set by email"""
    r.zadd('leaderboard', score, email)
    createLeaderboard()


def createLeaderboard(leaders=None, display=True):
    """Create the leaderboard at any given instant and print it from the given list of leaders.
        If leader list is not specified, assume the top ranings with no filters.
        Make sure all leader items carry scores"""
    if not display:
        return
    if leaders is None:
        leaders = r.zrevrange('leaderboard', 0, -1, withscores=True)
    users = []
    for leader in leaders:
        email = leader[0]
        hashKey = 'user_' + email
        userDetail = r.hgetall(hashKey)
        users.append(User(name=userDetail['name'], country=userDetail['country'],
                          email=leader[0], score=leader[1]))
    displayLeaderBoard(users)


def getTopHighest(k, country=None):
    """Get top k highest leaders. With an optional country filter"""
    if country is None:
        leaders = r.zrevrange('leaderboard', 0, k - 1, withscores=True)
        createLeaderboard(leaders)
    else:
        pass


def getUsersWithScore(score):
    """Get all users with a certain score"""
    leaders = r.zrevrangebyscore('leaderboard', score, score, withscores=True)
    createLeaderboard(leaders=leaders)


if __name__ == "__main__":
    # r.flushall()
    queryBuilder = QueryBuilder()
    aUser = User('Aman', 'India', 'a.in', 20)
    bUser = User('Saurbhi', 'India', 's.in', 15)
    cUser = User('Zaid', 'Pak', 'z.pk', 11)
    dUser = User('Nawaz', 'Pak', 'n.pk', 19)

    addUser(aUser.name, aUser.country, aUser.email, aUser.score, display=False)
    addUser(bUser.name, bUser.country, bUser.email, bUser.score, display=False)
    addUser(cUser.name, cUser.country, cUser.email, cUser.score, display=False)
    addUser(dUser.name, dUser.country, dUser.email, dUser.score, display=False)
    createLeaderboard(display=True)

    while True:
        userInput = [i for i in map(str.strip, input().split(' '))]
        queryBuilder.parse(userInput)
