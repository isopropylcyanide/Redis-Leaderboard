import sys
import redis

"""
A primitive interactive leaderboard designed in Python leveraging Redis
"""
r = redis.StrictRedis(host='localhost', port=6379, db=0,
                      charset="utf-8", decode_responses=True)

keyLeaderboard = 'leaderboard'
keyUserPrefix = 'user_'
keyLeaderboardCountryPrefix = 'leaderboard_country_'


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
    if len(users) == 0:
        prettyPrint('No records found')
        return
    print('*'*75)
    print('%3r | %15r | %10r | %12r | %10r' %
          ('RANK', 'EMAIL', 'NAME', 'COUNTRY', 'SCORE'))
    print('*'*75)
    for index, user in enumerate(users):
        print('%3r | %20r | %10r | %10r | %10r' %
              (index + 1, user.email, user.name, user.country, user.score))
    print('*'*75)


def prettyPrint(string):
    """Pretty print a simple string"""
    print('*'*75)
    print(string)
    print('*'*75)


COMMAND_LIST = {
    'UPSERT_USER': {
        'id': 1,
        'args': ['name', 'country', 'email'],
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
    'REMOVE_USER': {
        'id': 5,
        'args': ['email'],
        'optionalArgs': []
    }
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
            prettyPrint(
                'Invalid command specified. It has to be a valid string')
            return

        command = COMMAND_LIST[self.command]
        if len(self.inputParams[1:]) < len(command['args']):
            prettyPrint(self.command + ' is missing the required parameters')
            return

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
                name = self.inputParams[1]
            except IndexError:
                name = None
            try:
                score = self.inputParams[2]
            except IndexError:
                score = None
            try:
                country = self.inputParams[3]
            except IndexError:
                country = None
            search(name, score, country)

        elif self.command == 'REMOVE_USER':
            email = self.inputParams[1]
            removeUser(email)


def addUser(name, country, email, score=0, display=True):
    """Adds user properties by email hash and upsert score with 0
        Also add the user to the leaderboard of his country"""
    hashKey = keyUserPrefix + email
    country = country.capitalize()
    if r.exists(hashKey):
        prettyPrint('User ' + email + ' is already present. ')
    else:
        mapping = {
            'name': name,
            'country': country
        }
        r.hmset(hashKey, mapping)
        upsertScore(email, score, country=country, display=False)
        prettyPrint('User ' + email +
                    ' added to leaderboard with a score of %s. ' % (score))
        createLeaderboard(leaders=None, display=display)


def search(name=None, score=None, country=None):
    """Search on the entire leaderboard based on the optional filters name, score, country"""
    try:
        leaders = None
        if name is not None:
            if score is not None:
                if country is not None:
                    # find people locally by score and name
                    country = country.capitalize()
                    _leaderBoardKey = keyLeaderboardCountryPrefix + country
                    leaders = r.zrevrangebyscore(
                        _leaderBoardKey, score, score, withscores=True)
                    leaders = filter(lambda x: r.hget(
                        keyUserPrefix + x[0], 'name') == name, leaders)
                else:
                    # find people globally with given score and name
                    leaders = r.zrevrangebyscore(
                        keyLeaderboard, score, score, withscores=True)
                    leaders = filter(lambda x: r.hget(
                        keyUserPrefix + x[0], 'name') == name, leaders)
            else:
                # find people globally by name
                leaders = r.zrevrange(keyLeaderboard, 0, -1, withscores=True)
                leaders = filter(lambda x: r.hget(
                    keyUserPrefix + x[0], 'name') == name, leaders)
        createLeaderboard(leaders=leaders)
    except:
        prettyPrint('SEARCH Usage: SEARCH [NAME] [SCORE] [COUNTRY]')


def upsertScore(email, score, country=None, display=True):
    """Upsert score in the entire leaderboard as well as the country leaderboard"""
    hashKey = keyUserPrefix + email
    if not r.exists(hashKey):
        prettyPrint('User ' + email + ' doesn\'t exist.')
    else:
        r.zadd(keyLeaderboard, score, email)
        if country is None:
            hashKey = keyUserPrefix + email
            country = r.hget(hashKey, 'country')
        country = country.capitalize()
        r.zadd(keyLeaderboardCountryPrefix + country, score, email)
        createLeaderboard(display=display)


def createLeaderboard(leaders=None, display=True):
    """Create the leaderboard at any given instant and print it from the given list of leaders.
        If leader list is not specified, assume the top ranings with no filters.
        Make sure all leader items carry scores"""

    leaders = r.zrevrange(keyLeaderboard, 0, -1,
                          withscores=True) if leaders is None else leaders
    users = []
    for leader in leaders:
        email = leader[0]
        hashKey = keyUserPrefix + email
        userDetail = r.hgetall(hashKey)
        try:
            users.append(User(name=userDetail['name'], country=userDetail['country'],
                              email=leader[0], score=leader[1]))
        except KeyError:
            print('Couldn\'t fetch attributes for %s' % (email))
    if display:
        displayLeaderBoard(users)


def getTopHighest(k, country=None):
    """Get top k highest leaders. With an optional country filter"""
    if country is None:
        leaders = r.zrevrange(
            keyLeaderboard, 0, max(0, k - 1), withscores=True)
    else:
        country = country.capitalize()
        leaders = r.zrevrange(keyLeaderboardCountryPrefix +
                              country, 0, max(0, k - 1), withscores=True)
    createLeaderboard(leaders)


def getUsersWithScore(score):
    """Get all users with a certain score"""
    leaders = r.zrevrangebyscore(keyLeaderboard, score, score, withscores=True)
    createLeaderboard(leaders=leaders)


def removeUser(email):
    """Remove the user from the global leaderboard, country leaderboard 
        and purge their details """
    hashKey = keyUserPrefix + email
    if not r.exists(hashKey):
        prettyPrint('User ' + email + ' doesn\'t exists ')
    else:
        userDetail = r.hgetall(hashKey)
        _leaderBoardKey = keyLeaderboardCountryPrefix + userDetail['country']
        r.zrem(keyLeaderboard, email)
        r.zrem(_leaderBoardKey, email)
        r.delete(hashKey)
        prettyPrint(
            'User %s removed successfully from the global and country leaderboards' % (email))
        createLeaderboard()


if __name__ == "__main__":
    # r.flushall()
    queryBuilder = QueryBuilder()
    aUser = User('Aman', 'India', 'aman@redis.in', 30.91)
    cUser = User('Zaid', 'Pakistan', 'zaid@git.pk', 18.2)
    dUser = User('Nawaz', 'Saudi Arab', 'n.pk', 51.0)
    bUser = User('Saurbhi', 'India', 'sara@test.in', 37.10)
    dUser = User('Dean', 'USA', 'dean@me.us', 49.1)

    addUser(aUser.name, aUser.country, aUser.email, aUser.score, display=False)
    addUser(bUser.name, bUser.country, bUser.email, bUser.score, display=False)
    addUser(cUser.name, cUser.country, cUser.email, cUser.score, display=False)
    addUser(dUser.name, dUser.country, dUser.email, dUser.score, display=False)
    createLeaderboard(display=True)

    while True:
        userInput = [i for i in map(str.strip, input().strip(' ').split(' '))]
        queryBuilder.parse(userInput)
