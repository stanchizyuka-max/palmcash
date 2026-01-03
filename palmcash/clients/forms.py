"""
Forms for client and group management
"""
from django import forms
from django.core.exceptions import ValidationError
from .models import BorrowerGroup, GroupMembership, OfficerAssignment
from accounts.models import User


class GroupForm(forms.ModelForm):
    """Form for creating and updating borrower groups"""
    
    class Meta:
        model = BorrowerGroup
        fields = ['name', 'description', 'branch', 'payment_day', 'assigned_officer', 'max_members', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter group name',
                'required': True
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter group description (optional)'
            }),
            'branch': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter branch location',
                'required': True
            }),
            'payment_day': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Monday, Tuesday, or Day 1, Day 15',
                'required': True
            }),
            'assigned_officer': forms.Select(attrs={
                'class': 'form-control'
            }),
            'max_members': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Leave blank for unlimited',
                'min': 1
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
        help_texts = {
            'branch': 'Branch location where this group operates',
            'payment_day': 'Day when group members make payments (e.g., Monday for weekly, Day 15 for monthly)',
            'max_members': 'Maximum number of members allowed (leave blank for unlimited)',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Limit assigned_officer choices to loan officers only
        self.fields['assigned_officer'].queryset = User.objects.filter(
            role='loan_officer',
            is_active=True
        )
        self.fields['assigned_officer'].required = False
    
    def clean_name(self):
        """Validate group name is unique and not empty"""
        name = self.cleaned_data.get('name', '').strip()
        if not name:
            raise ValidationError('Group name is required.')
        
        # Check for uniqueness (excluding current instance if updating)
        queryset = BorrowerGroup.objects.filter(name__iexact=name)
        if self.instance.pk:
            queryset = queryset.exclude(pk=self.instance.pk)
        
        if queryset.exists():
            raise ValidationError(f'A group with the name "{name}" already exists.')
        
        return name
    
    def clean_branch(self):
        """Validate branch is not empty"""
        branch = self.cleaned_data.get('branch', '').strip()
        if not branch:
            raise ValidationError('Branch location is required.')
        return branch
    
    def clean_payment_day(self):
        """Validate payment_day is not empty"""
        payment_day = self.cleaned_data.get('payment_day', '').strip()
        if not payment_day:
            raise ValidationError('Payment day is required.')
        return payment_day
    
    def clean_max_members(self):
        """Validate max_members is positive if provided"""
        max_members = self.cleaned_data.get('max_members')
        if max_members is not None and max_members < 1:
            raise ValidationError('Maximum members must be at least 1.')
        return max_members


class GroupMembershipForm(forms.ModelForm):
    """Form for adding members to groups"""
    
    class Meta:
        model = GroupMembership
        fields = ['borrower', 'notes']
        widgets = {
            'borrower': forms.Select(attrs={
                'class': 'form-control',
                'required': True
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Optional notes about this membership'
            })
        }
    
    def __init__(self, *args, group=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.group = group
        
        # Only show borrowers who are not already active members of this group
        if group:
            self.fields['borrower'].queryset = User.objects.filter(
                role='borrower',
                is_active=True
            ).exclude(
                group_memberships__group=group,
                group_memberships__is_active=True
            )
        else:
            self.fields['borrower'].queryset = User.objects.filter(
                role='borrower',
                is_active=True
            )
    
    def clean(self):
        cleaned_data = super().clean()
        borrower = cleaned_data.get('borrower')
        
        if self.group and borrower:
            # Check if group is full
            if not self.group.can_add_member():
                raise ValidationError('This group is full or inactive.')
            
            # Check if borrower is already a member
            if GroupMembership.objects.filter(
                borrower=borrower,
                group=self.group,
                is_active=True
            ).exists():
                raise ValidationError(f'{borrower.full_name} is already a member of this group.')
        
        return cleaned_data


class OfficerAssignmentForm(forms.ModelForm):
    """Form for managing officer assignment settings"""
    
    class Meta:
        model = OfficerAssignment
        fields = ['max_groups', 'max_clients', 'is_accepting_assignments']
        widgets = {
            'max_groups': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 15,
                'required': True
            }),
            'max_clients': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'required': True
            }),
            'is_accepting_assignments': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
        help_texts = {
            'max_groups': 'Maximum number of groups this officer can manage (minimum 15)',
            'max_clients': 'Maximum number of individual clients this officer can handle',
            'is_accepting_assignments': 'Is this officer accepting new assignments?'
        }
    
    def clean_max_groups(self):
        """Validate max_groups is at least 15"""
        max_groups = self.cleaned_data.get('max_groups')
        if max_groups < 15:
            raise ValidationError('Maximum groups must be at least 15.')
        return max_groups
    
    def clean_max_clients(self):
        """Validate max_clients is positive"""
        max_clients = self.cleaned_data.get('max_clients')
        if max_clients < 1:
            raise ValidationError('Maximum clients must be at least 1.')
        return max_clients
