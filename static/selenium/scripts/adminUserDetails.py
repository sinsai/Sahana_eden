class AdminUserDetails:
    source = open("/home/sahana/Desktop/adminUser", "r")
    values = source.readlines()
    source.close()
    user = values[0]
    password = values[1]
