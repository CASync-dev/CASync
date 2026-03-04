# CASync

A platform for connecting timetables

## Premise

Users may create an accout (idealy SSO via uni account) and login to the paltform. Here they connect their timebale via ical sync (ideally we can somehow sync based on email but that may be unlikely). After syncing, users can add friends and create groups to share their schedules with. The principle display is a clander type view that shows who has a class when. We can do better than this. We shoudl have a day snap shot and a week snapshot. A firends list (view everyone) and a groups list (specifc groups of friends).  From these view users can see when friends or other members of the group have classes and when the overlap is. Users may also eventually add notes to these clases like marking a class as not actually attended, ect.

## Techincal considerations

### Backend

This would put a good amount of work into the backend. We need to consider:

- User auth system (perhaps sso also)
- User data storage (Timetables may be considered sensitive data)
  - Syncing: Time tables may change and need to be up to date
    - Just add sync on button
  - Need a privacy notice
- User relations (friends, groups)

### Middle ware

We need to be heavy on proepry user validation and authentication because of the sensitive data. Userres should only see what they must and have access to, no leaks are permitable. 

### Front end

This section is the most straightfoward i think but we do need to focus heabily on a readbale and clean calnder interface. I have seen some shit ones and it can turn people off. 

## Data

Ical info is our major data source. We can pull this via the cas ical link and convert to whatever we need.

## Feature list

- Edit calender item info:
  - Mark if going or not
  - Notes, ect
  - Users can mark of a whole day
- Custom items:
  - USers can add blocks of at uni time or busy time
    - Regular work hours
    - Stay at uni late days 
    - (Also reoccurring)
- University club feature
  - Clubs can make a group and add grou events. USers can subscribe.
  - This makes organising club events easy as they can see all members times
  - Can link to a post where users can find more info
- Study group items. 
  - Users can 'vote' on creating a study sesh
  - Can add detials, or propose changes, etc
  - Can be reoccurring
- Friends page:
  - Can see at a glance who is avialble now
  - Who is avialble soon
  - Busy or not on campus
  - Click on name to see full schedule
- Groups view
  - At a glance see all groups
  - On click see group cal
  - Options for making events, study seshes
- Pyblic and private groups
  - Users can have different privacy settings for what amount of info is shows:
    - Control what friends can see — full schedule, busy/free only, or nothing.

### If we have time

- A public broswing section
  - Find users who have similar schedules, subjects, ect
- Add suport for other uni systems