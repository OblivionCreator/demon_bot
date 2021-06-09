# Shopping System

with open('roles', 'r') as file:
    avail_roles = file.readlines()

    for i in avail_roles:
        ind = avail_roles.index(i)
        avail_roles[ind] = i[:-1]

print(avail_roles)