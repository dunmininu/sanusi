from django.core.management.base import BaseCommand
from business.models import Business
from accounts.models import User


class Command(BaseCommand):
    help = 'Fix business ownership based on business email addresses'

    def handle(self, *args, **options):
        try:
            businesses = Business.objects.all()
            users = User.objects.all()
            
            self.stdout.write('Fixing business ownership based on email addresses...')
            
            # Create a mapping of business emails to user emails
            email_mapping = {
                'alakaoluwaseyi@gmail.com': 'alakaoluwaseyi@gmail.com',
                'adebanjoaderinola@gmail.com': 'adebanjoaderinola@gmail.com',
                'zubulewo@pelagius.net': 'tarywy@forexzig.com',  # Assuming this belongs to tarywy
            }
            
            updated_count = 0
            
            for business in businesses:
                if business.email in email_mapping:
                    correct_owner_email = email_mapping[business.email]
                    correct_owner = users.filter(email=correct_owner_email).first()
                    
                    if correct_owner and business.owner != correct_owner:
                        old_owner = business.owner.email if business.owner else 'None'
                        business.owner = correct_owner
                        business.save()
                        updated_count += 1
                        
                        self.stdout.write(
                            f'Fixed: {business.name} | '
                            f'Old owner: {old_owner} | '
                            f'New owner: {correct_owner.email}'
                        )
                    elif not correct_owner:
                        self.stdout.write(
                            self.style.WARNING(
                                f'Warning: No user found for email {correct_owner_email} '
                                f'(Business: {business.name})'
                            )
                        )
                else:
                    self.stdout.write(
                        self.style.WARNING(
                            f'Warning: No mapping found for business email {business.email} '
                            f'(Business: {business.name})'
                        )
                    )
            
            self.stdout.write(f'\nUpdated {updated_count} businesses with correct owners')
            
            # Display final ownership
            self.stdout.write('\nFinal business ownership:')
            for business in businesses:
                owner_info = f'{business.owner.email}' if business.owner else 'No owner'
                self.stdout.write(f'Business: {business.name} | Owner: {owner_info}')
            
            self.stdout.write(
                self.style.SUCCESS('Successfully fixed business ownership!')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error: {str(e)}')
            ) 