from rest_framework import serializers

from apps.users.serializers import RoleSerializer, UserSerializer

from .models import DocumentWorkflow, StepAssignment, Workflow, WorkflowStep


class WorkflowStepSerializer(serializers.ModelSerializer):
    """Сериализатор шага маршрута (на чтение)"""

    role = RoleSerializer(read_only=True)

    class Meta:
        model = WorkflowStep
        fields = ["id", "step_order", "role"]
        read_only_fields = fields


class WorkflowStepCreateSerializer(serializers.ModelSerializer):
    """Сериализатор на создание шага маршрута"""

    class Meta:
        model = WorkflowStep
        fields = ["id", "step_order", "role"]

    def validate_step_order(self, value):
        """Проверяет уникальность порядкового номера в рамках маршрута"""
        workflow = self.context["workflow"]
        if WorkflowStep.objects.filter(workflow=workflow, step_order=value).exists():
            raise serializers.ValidationError(
                f"Шаг с порядковым номером {value} уже существует в этом маршруте"
            )
        return value


class WorkflowSerializer(serializers.ModelSerializer):
    """Сериализатор шаблона маршрута (на чтение)"""

    steps = WorkflowStepSerializer(many=True, read_only=True)

    class Meta:
        model = Workflow
        fields = ["id", "name", "description", "steps"]
        read_only_fields = fields


class WorkflowCreateSerializer(serializers.ModelSerializer):
    """Сериализатор на создание / обновление шаблона маршрута"""

    class Meta:
        model = Workflow
        fields = ["id", "name", "description"]


class StepAssignmentSerializer(serializers.ModelSerializer):
    """Сериализатор назначения на шаг (на чтение)"""

    assigned_user = UserSerializer(read_only=True)
    workflow_step = WorkflowStepSerializer(read_only=True)

    class Meta:
        model = StepAssignment
        fields = [
            "id",
            "workflow_step",
            "assigned_user",
            "assigned_at",
            "decision",
            "decided_at",
        ]
        read_only_fields = fields


class StepAssignmentCreateSerializer(serializers.ModelSerializer):
    """Сериализатор на создание назначения пользователя на шаг"""

    class Meta:
        model = StepAssignment
        fields = ["id", "workflow_step", "assigned_user"]

    def validate(self, attrs):
        """Проверяет принадлежность шага текущему DocumentWorkflow"""
        document_workflow = self.context["document_workflow"]
        workflow_step = attrs["workflow_step"]
        if workflow_step.workflow_id != document_workflow.workflow_id:
            raise serializers.ValidationError(
                "Шаг не принадлежит маршруту этого процесса"
            )
        return attrs


class DocumentWorkflowSerializer(serializers.ModelSerializer):
    """Сериализатор экземпляра процесса согласования (на чтение)"""

    workflow = WorkflowSerializer(read_only=True)
    assignments = StepAssignmentSerializer(many=True, read_only=True)
    current_step = serializers.SerializerMethodField()

    class Meta:
        model = DocumentWorkflow
        fields = ["id", "workflow", "assignments", "current_step"]
        read_only_fields = fields

    def get_current_step(self, obj):
        """Возвращает текущий активный шаг процесса"""
        assignment = obj.get_current_step()
        if assignment is None:
            return None
        return StepAssignmentSerializer(assignment).data


class StartWorkflowSerializer(serializers.Serializer):
    """Сериализатор запуска маршрута на документе"""

    workflow_id = serializers.IntegerField()

    def validate_workflow_id(self, value):
        """Проверяет существование маршрута"""
        if not Workflow.objects.filter(id=value).exists():
            raise serializers.ValidationError("Маршрут не найден")
        return value


class DecisionSerializer(serializers.Serializer):
    """Сериализатор решения по назначению"""

    decision = serializers.ChoiceField(choices=StepAssignment.Decision.choices)
