from django.db import models
from django.conf import settings


class Review(models.Model):
    contract = models.ForeignKey('contracts.Contract', on_delete=models.CASCADE)
    reviewer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reviews_given')
    reviewee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reviews_received')
    rating = models.PositiveIntegerField(default=5)
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.reviewer.username + ' -> ' + self.reviewee.username + ' (' + str(self.rating) + '/5)'
