import json
from pathlib import Path
from pydantic import BaseModel, ConfigDict, Field, model_validator


class Target(BaseModel):
    model_config = ConfigDict(extra='forbid')
    standard_code: str = Field(min_length=1)
    version: str = Field(min_length=1)
    clause: str | None = None


class Question(BaseModel):
    model_config = ConfigDict(extra='forbid')
    id: str = Field(min_length=1)
    question: str = Field(min_length=2)
    domain: str
    expected_documents: list[Target] = Field(default_factory=list)
    expected_clauses: list[Target] = Field(default_factory=list)
    # Each group is a required evidence need; any member satisfies that need.
    clause_groups: list[list[Target]] = Field(default_factory=list)
    expected_keywords: list[str] = Field(default_factory=list)
    negative: bool = False
    notes: str = ''
    applicable_conditions: str = ''

    @model_validator(mode='after')
    def validate_targets(self):
        clauses = self.expected_clauses + [t for g in self.clause_groups for t in g]
        if any(t.clause is not None for t in self.expected_documents):
            raise ValueError('Document targets must not contain clause numbers')
        if any(not t.clause for t in clauses) or any(not g for g in self.clause_groups):
            raise ValueError('Clause targets require clause numbers and nonempty groups')
        if self.expected_clauses and self.clause_groups:
            raise ValueError('Use expected_clauses OR clause_groups')
        if self.negative and (self.expected_documents or clauses):
            raise ValueError('Negative questions cannot have expected evidence')
        if not self.negative and (not self.expected_documents or not clauses):
            raise ValueError('Positive questions require document and clause targets')
        if any((t.standard_code, t.version) not in {(d.standard_code, d.version) for d in self.expected_documents} for t in clauses):
            raise ValueError('Clause documents must be listed in expected_documents')
        return self

    def groups(self):
        return self.clause_groups or [[t] for t in self.expected_clauses]


def load_dataset(path):
    data = json.loads(Path(path).read_text(encoding='utf-8-sig'))
    if not isinstance(data, list) or not data:
        raise ValueError('Dataset must be a nonempty JSON array')
    questions = [Question.model_validate(row) for row in data]
    if len({q.id for q in questions}) != len(questions):
        raise ValueError('Duplicate question IDs')
    return questions
