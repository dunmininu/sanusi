import json
from rest_framework import serializers
from django.shortcuts import get_object_or_404
from .models import Business
from business.private.models import KnowledgeBase, EscalationDepartment
from sanusi.views import generate_response_chat


class KnowledgeBaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = KnowledgeBase
        fields = [
            "title",
            "content",
            "knowledgebase_id",
            "is_company_description",
            "cleaned_data",
        ]
        extra_kwargs = {"cleaned_data": {"read_only": True}}

    def create(self, validated_data):
        title = validated_data["title"]
        content = validated_data["content"]
        knowledgebase_id = validated_data["knowledgebase_id"]
        is_company_description = validated_data["is_company_description"]
        company_id = self.context.get("company_id")

        business = get_object_or_404(Business, company_id=company_id)

        prompt = [
            {
                "role": "system",
                "content": "Clean this data into a reusable json content that openai chat can understand and use for response processing later not more than 512 characters",
            },
            {
                "role": "user",
                "content": f"data to be cleaned {content}",
            },
        ]
        response = generate_response_chat(prompt, 400)

        try:
            cleaned_data = json.dumps(response["choices"][0]["message"]["content"])
        except Exception as e:
            print("An error occurred:", str(e))
            cleaned_data = response["choices"][0]["message"]["content"]

        kb = KnowledgeBase.objects.create(
            title=title,
            content=content,
            knowledgebase_id=knowledgebase_id,
            is_company_description=is_company_description,
            cleaned_data=cleaned_data,
            business=business,
        )

        return kb


class BulkCreateKnowledgeBaseSerializer(serializers.ListSerializer):
    child = KnowledgeBaseSerializer()

    def create(self, validated_data):
        knowledge_bases = []
        for item in validated_data:
            kb_serializer = KnowledgeBaseSerializer(data=item, context=self.context)
            if kb_serializer.is_valid():
                knowledge_base = kb_serializer.save()
                knowledge_bases.append(knowledge_base)
        return knowledge_bases


class KnowledgeBaseDeleteSerializer(serializers.Serializer):
    knowledgebase_id = serializers.CharField(required=False, allow_null=True)


class KnowledgeBaseBulkUpdateSerializer(serializers.ListSerializer):
    child = KnowledgeBaseSerializer()


class EscalationDepartmentSeralizer(serializers.ModelSerializer):
    class Meta:
        model = EscalationDepartment
        fields = ["name"]


class BusinessSerializer(serializers.ModelSerializer):
    escalation_departments = EscalationDepartmentSeralizer(many=True)
    knowledge_base = serializers.SerializerMethodField()

    class Meta:
        model = Business
        fields = [
            "name",
            "company_id",
            "escalation_departments",
            "reply_instructions",
            "knowledge_base",
        ]
        read_only_fields = ["company_id"]

    def get_knowledge_base(self, business):
        knowledge_base = KnowledgeBase.objects.filter(
            business=business, is_company_description=True
        ).first()
        return KnowledgeBaseSerializer(knowledge_base).data if knowledge_base else None

    def validate(self, data):
        """
        Validate the serializer data before creating the Business instance.
        """
        if (
            "company_id" in data
            and Business.objects.filter(company_id=data["company_id"]).exists()
        ):
            raise serializers.ValidationError("Company ID already exists")
        return data

    def create(self, validated_data):
        escalation_departments_data = validated_data.pop("escalation_departments")
        business = Business.objects.create(**validated_data)

        for department_data in escalation_departments_data:
            EscalationDepartment.objects.create(business=business, **department_data)

        return business

    def update(self, instance, validated_data):
        escalation_departments_data = validated_data.pop("escalation_departments", None)
        instance.name = validated_data.get("name", instance.name)
        instance.email = validated_data.get("email", instance.email)
        instance.reply_instructions = validated_data.get(
            "reply_instructions", instance.reply_instructions
        )
        instance.save()

        if escalation_departments_data is not None:
            # delete old departments
            instance.escalation_departments.all().delete()
            # create new departments
            for department_data in escalation_departments_data:
                EscalationDepartment.objects.create(
                    business=instance, **department_data
                )

        return instance


class EnifBusinessCreateSerializer(serializers.Serializer):
    company_id = serializers.CharField(required=False, allow_null=True)
    business_name = serializers.CharField(required=False, allow_null=True)
    knowledge_base = serializers.ListField(required=False, allow_null=True)
    instructions = serializers.CharField(required=False, allow_null=True)
    escalation_departments = serializers.ListField(required=False, allow_null=True)
