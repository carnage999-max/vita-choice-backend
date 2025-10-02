from django.db import models

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
    
    
