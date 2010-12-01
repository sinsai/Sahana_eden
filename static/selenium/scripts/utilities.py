
class Utilities:

    # a file with one user on each line
    # The user details are first_name, last_name, email, password [, roles] 
    def getUserDetails(self):
        source = open("../data/user.txt", "r")
        values = source.readlines()
        source.close()
        return values
