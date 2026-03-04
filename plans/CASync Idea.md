# CASync

A tool for connecting timetables

## Premise

Users may create an accout (idealy SSO via uni account) and login to the paltform. Here they connect their timebale via ical sync (ideally we can somehow sync based on email but that may be unlikely). After sybcing, users can add friends and create groups to share their schedules with. The principle display is a clander type view that shows who has a class when. We can do better than this. We shoudl have. day snap shot and a week snapshot. A firends list (view everyone) and a groups list (specifc groups of friends).  From these view users can see when friends or other members of the group have classes and when the overlap is. Users may also eventually add notes to these clases like marking a class as not actually attended, ect.

## Techincal considerations

### Backend

This would put a good amount of work into the backend. We need to consider:

- User auth system (perhaps sso also)
- User data storage (Timetables may be considered sensitive data)
  - Syncing: Time tables may change and need to be up to date
- User relations (friends, groups)

### Middle ware

We need to be heavy on proepry user validation and authentication because of the sensitive data. Userres should only see what they must and have access to, no leaks are permitable. 

### Front end

This section is the most straightfoward i think but we do need to focus heabily on a readbale and clean calnder interface. I have seen some shit ones and it can turn people off. 