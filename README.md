# Redis Leaderboard
A primitive interactive leaderboard designed in Python leveraging Redis running on the localhost.

### What is it? ###
----
A primitive interactive leaderboard with non duplicate designed in Python leveraging Redis. For the purposes of demonstration,
a very primitive user model has been constructured as following.

```

class User:
    """A model user having a name, country, email and a score"""

    def __init__(self, name, country, email score=0):
        self.name = name
        self.email = email
        self.country = country
        self.score = score

```
Moreover, it's been assumed that the primary key for any user is it's *email*.
The decision as to why the *email* was chosen as the primary key is because in any major competetion that boasts
of a leaderboard, the players always have either a unique username or a unique email.
People are welcome to switch email to usernames.

### Prerequisites ###
---
* Python 3.6.1 or above.
* Redis python library. To install

    ```$pip install redis```

### How do I get started ###
---
* Fire up a terminal. 

    ```$ python redis-leaderboard.py```

   * The program shall run an event loop during which you are free to enter commands so as to modify the leaderboard.
   * Every command returns a pretty human readable message/current state of the leaderboard.
   * Program, by default refers to redis synchronously. Hence, changes made during one instance of program would 
     continue to persist. To avoid persistent, uncomment ```r.flushall()```

### Command list ###
---

* #### UPSERT_USER  ####
Upserts a user into the current leaderboard. The uniqueness for the user is guaranteed by the email.
Throws an error if the user with the same email is being entered again.
  A default score of 0 will be set onto the leaderboard for the user.
```
  $ UPSERT_USER <NAME> <COUNTRY> <EMAIL>
```


* #### UPSERT_SCORE ####
Upserts the score of the user with the given email and the given numeric value. If no such user by that email
exists is throws an error. Upserting an existing score of *30* with *40* will simply replace it with *40*
```
  UPSERT_SCORE <NAME> <COUNTRY> <EMAIL>
```
---

* #### GET_TOP ####
Gets the top K users by rank. If rank is specified as 0, the topper is returned. This command takes in an optional
<country> which filters the users and then returns the top K users.
```
  GET_TOP <RANK> [COUNTRY]
```
---
  
* #### GET_USERS_WITH_SCORE ####
Gets all the users with the given score in the leaderboard.
```
  GET_USERS_WITH_SCORE <SCORE> 
```
---

* #### SEARCH ####
Performs a search on the current leaderboard. It takes in three optional params *name*, *score* and *country*.
   * If no param is specified it displays the entire leaderboard.
   * If name is specified, searches leaderbard by name
   * If name and score is specified, filters result of above by score
   * If name, score and country is specified, filters result of above by country
```
  SEARCH [NAME] [SCORE] [COUNTRY]
```
---


* #### REMOVE_USER ####
Removes the user from the global as well as country leaderboard and purges its information. If no such
user is present it throws and error.
```
  REMOVE_USER <EMAIL>
```



 
