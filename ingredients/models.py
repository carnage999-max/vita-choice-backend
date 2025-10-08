from django.db import models
from django.contrib.auth import get_user_model


User = get_user_model()


class Ingredient(models.Model):
    name = models.CharField(max_length=255, unique=True, db_index=True)
    category = models.CharField(max_length=100, db_index=True, blank=True)
    source = models.CharField(max_length=100, blank=True)
    safety = models.CharField(max_length=100, blank=True)
    evidence = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['name', 'category']),
            models.Index(fields=['safety']),
        ]
    
    def __str__(self):
        return self.name
    
    @property
    def safety_level(self):
        """Auto-classify safety: SAFE, CAUTION, or RISK"""
        safety_lower = self.safety.lower()
        
        if 'general dietary use' in safety_lower:
            return 'SAFE'
        elif any(word in safety_lower for word in ['caution', 'topical', 'external', 'processing required', 'alkaloids']):
            return 'CAUTION'
        elif any(word in safety_lower for word in ['restricted', 'controlled', 'high-risk']):
            return 'RISK'
        else:
            return 'UNKNOWN'
    
    @property
    def safety_color(self):
        """Return color code for UI"""
        colors = {
            'SAFE': '#4caf50',
            'CAUTION': '#ff9800',
            'RISK': '#f44336',
            'UNKNOWN': '#757575'
        }
        return colors.get(self.safety_level, '#757575')
    

class Formula(models.Model):
    """User-created supplement formulas"""
    
    REGION_CHOICES = [
        ('US', 'United States'),
        ('EU', 'European Union'),
        ('CA', 'Canada'),
        ('AU', 'Australia'),
    ]
    
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='formulas')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    region = models.CharField(max_length=2, choices=REGION_CHOICES, default='US')
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['owner', '-updated_at']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.owner.username})"
    
    def total_weight_mg(self):
        """Calculate total weight in milligrams"""
        total = 0
        for item in self.items.all():
            if item.dose_unit == 'g':
                total += float(item.dose_value) * 1000
            elif item.dose_unit == 'mcg':
                total += float(item.dose_value) / 1000
            elif item.dose_unit == 'mg':
                total += float(item.dose_value)
            # IU doesn't convert to weight, skip
        return round(total, 2)
    
    def ingredient_count(self):
        """Count of ingredients in formula"""
        return self.items.count()
    
    def check_compliance(self):
        """
        Check formula compliance based on ingredient safety levels
        Returns dict with status and issues
        """
        issues = []
        risk_count = 0
        caution_count = 0
        safe_count = 0
        
        for item in self.items.select_related('ingredient').all():
            ingredient = item.ingredient
            level = ingredient.safety_level
            
            if level == 'RISK':
                risk_count += 1
                issues.append({
                    'ingredient_id': ingredient.id,
                    'ingredient': ingredient.name,
                    'dose': f"{item.dose_value}{item.dose_unit}",
                    'category': ingredient.category,
                    'severity': 'RISK',
                    'level': level,
                    'safety_info': ingredient.safety,
                    'message': f'{ingredient.safety}. This ingredient is restricted/controlled and requires regulatory review.',
                    'action': 'Review regulatory requirements before use'
                })
            
            elif level == 'CAUTION':
                caution_count += 1
                
                # Specific messages based on safety text
                safety_lower = ingredient.safety.lower()
                if 'topical' in safety_lower or 'external' in safety_lower:
                    message = f'{ingredient.safety}. This ingredient is for external use only and should not be included in oral supplements.'
                    action = 'Remove from oral supplement formula or verify alternative approved use'
                elif 'alkaloids' in safety_lower or 'processing required' in safety_lower:
                    message = f'{ingredient.safety}. Special processing or preparation is required.'
                    action = 'Verify proper processing methods are applied'
                else:
                    message = f'{ingredient.safety}. Use with caution.'
                    action = 'Review usage guidelines and dosage limits'
                
                issues.append({
                    'ingredient_id': ingredient.id,
                    'ingredient': ingredient.name,
                    'dose': f"{item.dose_value}{item.dose_unit}",
                    'category': ingredient.category,
                    'severity': 'CAUTION',
                    'level': level,
                    'safety_info': ingredient.safety,
                    'message': message,
                    'action': action
                })
            
            elif level == 'SAFE':
                safe_count += 1
        
        # Determine overall status
        if risk_count > 0:
            status = 'STOP'
            status_message = f'Formula contains {risk_count} restricted/high-risk ingredient(s). Cannot proceed without regulatory approval.'
            can_proceed = False
        elif caution_count > 0:
            status = 'WARNING'
            status_message = f'Formula contains {caution_count} ingredient(s) that require attention. Review warnings before proceeding.'
            can_proceed = True
        else:
            status = 'APPROVED'
            status_message = 'All ingredients are approved for general dietary use. Formula is compliant.'
            can_proceed = True
        
        return {
            'status': status,
            'status_message': status_message,
            'can_proceed': can_proceed,
            'total_ingredients': self.items.count(),
            'summary': {
                'safe': safe_count,
                'caution': caution_count,
                'risk': risk_count
            },
            'issues': issues
        }


class FormulaItem(models.Model):
    """Individual ingredients in a formula with dosage"""
    
    UNIT_CHOICES = [
        ('mg', 'Milligrams'),
        ('mcg', 'Micrograms'),
        ('g', 'Grams'),
        ('IU', 'International Units'),
    ]
    
    formula = models.ForeignKey(
        Formula, 
        related_name='items',
        on_delete=models.CASCADE
    )
    ingredient = models.ForeignKey(Ingredient, on_delete=models.PROTECT)
    dose_value = models.DecimalField(max_digits=10, decimal_places=2)
    dose_unit = models.CharField(max_length=10, choices=UNIT_CHOICES, default='mg')
    notes = models.TextField(blank=True)
    
    # Order in formula
    order = models.PositiveIntegerField(default=0)
    
    class Meta:
        unique_together = ['formula', 'ingredient']
        ordering = ['order', 'ingredient__name']
    
    def __str__(self):
        return f"{self.ingredient.name}: {self.dose_value}{self.dose_unit}"

