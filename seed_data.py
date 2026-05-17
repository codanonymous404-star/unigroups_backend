import django, os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'unigroups_project.settings')
django.setup()

from users.models import User
from groups.models import Group, GroupMember, JoinRequest

# Clear
JoinRequest.objects.all().delete()
GroupMember.objects.all().delete()
Group.objects.all().delete()
User.objects.all().delete()

print("🌱 Seeding...")

# Admin
admin = User.objects.create_superuser(
    roll_number='SU00-ADMIN-A00-001', name='Admin User',
    email='admin@superior.edu.pk', password='admin123'
)

# SE Students
se = []
for rn, name, email in [
    ('SU72-BSSEM-F25-001','Ali Hassan',  'ali@superior.edu.pk'),
    ('SU72-BSSEM-F25-002','Sara Khan',   'sara@superior.edu.pk'),
    ('SU72-BSSEM-F25-003','Usman Tariq', 'usman@superior.edu.pk'),
    ('SU72-BSSEM-F25-004','Hamza Saeed', 'hamza@superior.edu.pk'),
    ('SU72-BSSEM-F25-005','Nida Fatima', 'nida@superior.edu.pk'),
]:
    se.append(User.objects.create_user(roll_number=rn, name=name, email=email,
                                        password='pass1234', department='SE', is_verified=True))

# CS Students
cs = []
for rn, name, email in [
    ('SU72-BSCS-F25-001','Bilal Ahmed', 'bilal@superior.edu.pk'),
    ('SU72-BSCS-F25-002','Zara Sheikh', 'zara@superior.edu.pk'),
    ('SU72-BSCS-F25-003','Omar Farooq', 'omar@superior.edu.pk'),
    ('SU72-BSCS-F25-004','Amna Raza',   'amna@superior.edu.pk'),
]:
    cs.append(User.objects.create_user(roll_number=rn, name=name, email=email,
                                        password='pass1234', department='CS', is_verified=True))

# SE Groups
g1 = Group.objects.create(name='Alpha Dev Squad', department='SE', description='Full-stack web project.', max_members=5, created_by=se[0])
GroupMember.objects.create(group=g1, user=se[0], role='leader')
GroupMember.objects.create(group=g1, user=se[1], role='member')
GroupMember.objects.create(group=g1, user=se[2], role='member')
JoinRequest.objects.create(group=g1, user=se[3], message='I want to join!')

g2 = Group.objects.create(name='SE Research Group', department='SE', description='AI research.', max_members=4, created_by=se[3])
GroupMember.objects.create(group=g2, user=se[3], role='leader')
GroupMember.objects.create(group=g2, user=se[4], role='member')

# CS Groups
g3 = Group.objects.create(name='CS Innovators', department='CS', description='Cloud computing project.', max_members=4, created_by=cs[0])
GroupMember.objects.create(group=g3, user=cs[0], role='leader')
GroupMember.objects.create(group=g3, user=cs[1], role='member')

g4 = Group.objects.create(name='Data Science Lab', department='CS', description='ML experiments.', max_members=5, created_by=cs[2])
GroupMember.objects.create(group=g4, user=cs[2], role='leader')
GroupMember.objects.create(group=g4, user=cs[3], role='member')

print(f"✓ {User.objects.count()} users")
print(f"✓ {Group.objects.count()} groups")
print(f"✓ {GroupMember.objects.count()} memberships")
print(f"✓ {JoinRequest.objects.count()} join requests")
print("\n✅ Done!")
print("\nLogin credentials:")
print("  Admin: SU00-ADMIN-A00-001  / admin123")
print("  SE:    SU72-BSSEM-F25-001  / pass1234")
print("  CS:    SU72-BSCS-F25-001   / pass1234")
