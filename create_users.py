import django, os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pharmaerp.settings")
django.setup()

from django.contrib.auth.models import User, Group

print("=== CREATING USERS & ROLES ===")

# Create Groups
groups_names = ["Administrateur", "Pharmacien", "Caissier", "ResponsableDepot"]
for name in groups_names:
    grp, created = Group.objects.get_or_create(name=name)
    print(f"  {'Created' if created else 'Exists'}: {name}")

# Create test users
users_data = [
    ("pharmacien1", "pharma123", "Pharmacien", False, False),
    ("caissier1", "caissier123", "Caissier", False, False),
    ("depot1", "depot123", "ResponsableDepot", False, False),
]

for username, password, group_name, is_staff, is_super in users_data:
    user, created = User.objects.get_or_create(
        username=username,
        defaults={"is_staff": is_staff, "is_superuser": is_super}
    )
    if created:
        user.set_password(password)
        user.save()
    
    grp = Group.objects.get(name=group_name)
    user.groups.add(grp)
    print(f"  User: {username} / Password: {password} / Role: {group_name}")

print("\n=== DONE ===")
print("\nLogin avec:")
print("  admin / JAZ051236 (Administrateur)")
print("  pharmacien1 / pharma123 (Pharmacien)")
print("  caissier1 / caissier123 (Caissier)")
print("  depot1 / depot123 (Responsable Depot)")
