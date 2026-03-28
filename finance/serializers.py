from rest_framework import serializers
from .models import Transaction


class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = '__all__'

    def validate(self, attrs):
        """§3.5 categories must match income vs expense type."""
        inst = self.instance
        ttype = attrs.get('transaction_type')
        if ttype is None and inst is not None:
            ttype = inst.transaction_type
        cat = attrs.get('category')
        if cat is None and inst is not None:
            cat = inst.category
        if ttype is None or cat is None:
            return attrs
        if ttype == 'income':
            valid = {c[0] for c in Transaction.INCOME_CATEGORY_CHOICES}
        else:
            valid = {c[0] for c in Transaction.EXPENSE_CATEGORY_CHOICES}
        if cat not in valid:
            raise serializers.ValidationError(
                {'category': f'Invalid category for {ttype}. Allowed: {sorted(valid)}'}
            )
        return attrs
