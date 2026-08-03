"""Deterministic in-memory agent runtime used for the demo and tests.

It produces stable, schema-valid output for every agent role WITHOUT any API
key, so the whole workflow can be demonstrated offline.
"""

from __future__ import annotations

from adf.domain.contracts import (
    ClarificationQuestionContract,
    EpicContract,
    GherkinScenario,
    ProductOwnerAnalysis,
    QAContract,
    ReviewContract,
    ReviewFinding,
    StoryContract,
)
from adf.domain.enums import Priority, QuestionAnswerType
from adf.ports.agent_runtime import AgentRequest, AgentResult, TOutput


class MockAgentRuntime:
    """Deterministic runtime. Same input -> same output."""

    provider = "mock"

    async def run(
        self,
        request: AgentRequest,
        output_model: type[TOutput],
    ) -> tuple[TOutput, AgentResult]:
        builder = _BUILDERS.get(output_model)
        if builder is None:
            raise TypeError(f"MockAgentRuntime cannot build {output_model.__name__}")
        instance = builder(request)
        # ``builder`` returns the correct concrete model; cast for the checker.
        output = output_model.model_validate(instance.model_dump())
        result = AgentResult(
            output_summary=_summarize(instance),
            provider=self.provider,
            model="mock-deterministic-1",
            tokens_input=len(str(request.context)) // 4,
            tokens_output=64,
            raw={"role": request.role.value},
        )
        return output, result


def _summarize(instance: object) -> str:
    if isinstance(instance, ProductOwnerAnalysis):
        return (
            f"{len(instance.questions)} question(s), "
            f"{len(instance.stories)} story(ies) generated"
        )
    if isinstance(instance, ReviewContract):
        return f"Review verdict: {instance.verdict}"
    if isinstance(instance, QAContract):
        return f"QA verdict: {instance.verdict}"
    return "ok"


def _has_answers(request: AgentRequest) -> bool:
    answers = request.context.get("answers")
    return bool(answers)


def _build_product_owner(request: AgentRequest) -> ProductOwnerAnalysis:
    raw = str(request.context.get("raw_request", "")).lower()
    is_password_reset = any(
        kw in raw for kw in ("mot de passe", "password", "réinitialis", "reset")
    )
    answered = _has_answers(request)

    if is_password_reset:
        return _password_reset_analysis(answered, request)
    return _generic_analysis(answered, request)


def _password_reset_analysis(answered: bool, request: AgentRequest) -> ProductOwnerAnalysis:
    questions: list[ClarificationQuestionContract] = []
    if not answered:
        questions = [
            ClarificationQuestionContract(
                question="Par quel canal le lien de réinitialisation doit-il être envoyé ?",
                answer_type=QuestionAnswerType.SINGLE_CHOICE,
                options=["Email", "SMS", "Email et SMS"],
                blocking=True,
            ),
            ClarificationQuestionContract(
                question="Quelle est la durée de validité du lien de réinitialisation ?",
                answer_type=QuestionAnswerType.SINGLE_CHOICE,
                options=["15 minutes", "1 heure", "24 heures"],
                blocking=True,
            ),
            ClarificationQuestionContract(
                question=(
                    "Quel comportement adopter lorsqu'une adresse email inconnue est saisie ?"
                ),
                answer_type=QuestionAnswerType.SINGLE_CHOICE,
                options=[
                    "Répondre de façon neutre (anti-énumération)",
                    "Indiquer que l'adresse n'existe pas",
                ],
                blocking=True,
            ),
        ]

    epic = EpicContract(
        title="Réinitialisation de mot de passe en libre-service",
        description=(
            "Permettre à un utilisateur de récupérer l'accès à son compte via un "
            "lien de réinitialisation sécurisé."
        ),
        business_value=(
            "Réduit les demandes au support et le taux d'abandon lié aux comptes "
            "verrouillés."
        ),
    )

    if not answered:
        # Not enough info yet: no stories until questions are answered.
        return ProductOwnerAnalysis(
            normalized_request=(
                "En tant qu'utilisateur, je veux réinitialiser mon mot de passe pour "
                "récupérer l'accès à mon compte."
            ),
            assumptions=["Le compte est identifié par une adresse email."],
            risks=[
                "Énumération de comptes si les réponses ne sont pas neutres.",
                "Jetons de réinitialisation réutilisables s'ils n'expirent pas.",
            ],
            business_rules=[
                "Un lien de réinitialisation doit être à usage unique.",
                "Un lien expiré ne doit jamais permettre de changer le mot de passe.",
            ],
            questions=questions,
            epic=epic,
            stories=[],
        )

    stories = [
        StoryContract(
            title="Demander un lien de réinitialisation",
            description=(
                "L'utilisateur saisit son email et reçoit un lien à usage unique."
            ),
            acceptance_criteria=[
                "Un email valide déclenche l'envoi d'un lien.",
                "La réponse est neutre pour ne pas révéler l'existence du compte.",
                "Le lien expire selon la durée configurée.",
            ],
            gherkin=[
                GherkinScenario(
                    title="Demande avec un email existant",
                    steps=[
                        "Given un compte existe pour l'email fourni",
                        "When l'utilisateur demande une réinitialisation",
                        "Then un lien à usage unique est envoyé",
                        "And la réponse HTTP est neutre",
                    ],
                ),
                GherkinScenario(
                    title="Demande avec un email inconnu",
                    steps=[
                        "Given aucun compte n'existe pour l'email fourni",
                        "When l'utilisateur demande une réinitialisation",
                        "Then aucune information sur l'existence du compte n'est révélée",
                    ],
                ),
            ],
            priority=Priority.HIGH,
            estimated_complexity=3,
            dependencies=[],
        ),
        StoryContract(
            title="Consommer le lien et définir un nouveau mot de passe",
            description="L'utilisateur ouvre le lien et choisit un nouveau mot de passe.",
            acceptance_criteria=[
                "Un jeton valide et non expiré permet de changer le mot de passe.",
                "Un jeton expiré ou déjà utilisé est refusé avec un message clair.",
                "Le mot de passe respecte la politique de complexité.",
            ],
            gherkin=[
                GherkinScenario(
                    title="Jeton valide",
                    steps=[
                        "Given un jeton valide et non expiré",
                        "When l'utilisateur soumet un nouveau mot de passe conforme",
                        "Then le mot de passe est mis à jour",
                        "And le jeton est invalidé",
                    ],
                ),
                GherkinScenario(
                    title="Jeton expiré",
                    steps=[
                        "Given un jeton expiré",
                        "When l'utilisateur tente de changer son mot de passe",
                        "Then l'opération est refusée",
                    ],
                ),
            ],
            priority=Priority.HIGH,
            estimated_complexity=5,
            dependencies=["Demander un lien de réinitialisation"],
        ),
    ]

    return ProductOwnerAnalysis(
        normalized_request=(
            "En tant qu'utilisateur, je veux réinitialiser mon mot de passe pour "
            "récupérer l'accès à mon compte."
        ),
        assumptions=["Le canal et la durée retenus proviennent des réponses fournies."],
        risks=["Énumération de comptes si la réponse n'est pas neutre."],
        business_rules=[
            "Le lien est à usage unique.",
            "Le lien expire selon la durée choisie.",
        ],
        questions=[],
        epic=epic,
        stories=stories,
    )


def _generic_analysis(answered: bool, request: AgentRequest) -> ProductOwnerAnalysis:
    raw = str(request.context.get("raw_request", "")).strip() or "Nouvelle demande"
    questions: list[ClarificationQuestionContract] = []
    if not answered:
        questions = [
            ClarificationQuestionContract(
                question="Quel est le résultat attendu principal de cette demande ?",
                answer_type=QuestionAnswerType.FREE_TEXT,
                options=[],
                blocking=True,
            )
        ]
    epic = EpicContract(
        title=raw[:80],
        description=raw,
        business_value="Apporte de la valeur à l'utilisateur final.",
    )
    stories: list[StoryContract] = []
    if answered:
        stories = [
            StoryContract(
                title=f"Implémenter: {raw[:60]}",
                description=raw,
                acceptance_criteria=["Le comportement décrit est disponible."],
                gherkin=[
                    GherkinScenario(
                        title="Cas nominal",
                        steps=[
                            "Given le contexte décrit",
                            "When l'utilisateur effectue l'action",
                            "Then le résultat attendu est obtenu",
                        ],
                    )
                ],
                priority=Priority.MEDIUM,
                estimated_complexity=3,
                dependencies=[],
            )
        ]
    return ProductOwnerAnalysis(
        normalized_request=raw,
        assumptions=[],
        risks=[],
        business_rules=[],
        questions=questions,
        epic=epic,
        stories=stories,
    )


def _build_review(request: AgentRequest) -> ReviewContract:
    ci_state = str(request.context.get("ci_state", "success")).lower()
    if ci_state == "failure":
        return ReviewContract(
            summary="La CI est en échec, la revue ne peut pas approuver.",
            findings=[ReviewFinding(severity="blocking", message="CI en échec.")],
            verdict="changes_requested",
        )
    return ReviewContract(
        summary="Le code respecte les critères d'acceptation et la CI est verte.",
        findings=[
            ReviewFinding(severity="suggestion", message="Ajouter un cas de test limite.")
        ],
        verdict="approved",
    )


def _build_qa(request: AgentRequest) -> QAContract:
    ci_state = str(request.context.get("ci_state", "success")).lower()
    verdict = "fail" if ci_state == "failure" else "pass"
    return QAContract(
        summary="Scénarios nominaux et d'erreur vérifiés.",
        scenarios_checked=["Cas nominal", "Cas d'erreur", "Contrôle des droits"],
        missing_tests=[] if verdict == "pass" else ["Cas de concurrence"],
        verdict=verdict,
    )


_BUILDERS = {
    ProductOwnerAnalysis: _build_product_owner,
    ReviewContract: _build_review,
    QAContract: _build_qa,
}
