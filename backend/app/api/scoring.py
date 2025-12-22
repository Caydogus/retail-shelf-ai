from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict
from pydantic import BaseModel
from datetime import datetime

from app.models.database import get_db, ScoringRule, Company
from app.ai.scoring_engine import ScoringEngine

router = APIRouter()


# Pydantic Schemas
class ScoringRuleCreate(BaseModel):
    company_id: int
    rule_name: str
    rule_type: str  # shelf_coverage, product_visibility, planogram_compliance, color_match
    weight: float = 1.0
    parameters: Dict = None


class ScoringRuleResponse(BaseModel):
    id: int
    company_id: int
    rule_name: str
    rule_type: str
    weight: float
    parameters: Dict = None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class ScoreCalculationRequest(BaseModel):
    shelf_coverage: float
    visibility_score: float
    expected_distribution: Dict = None
    actual_distribution: Dict = None
    color_matches: Dict = None
    custom_weights: Dict = None


# Create Scoring Rule
@router.post("/", response_model=ScoringRuleResponse)
def create_scoring_rule(rule: ScoringRuleCreate, db: Session = Depends(get_db)):
    company = db.query(Company).filter(Company.id == rule.company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    # Validate rule type
    valid_types = ["shelf_coverage", "product_visibility", "planogram_compliance", "color_match"]
    if rule.rule_type not in valid_types:
        raise HTTPException(status_code=400, detail=f"Invalid rule type. Must be one of: {valid_types}")
    
    new_rule = ScoringRule(
        company_id=rule.company_id,
        rule_name=rule.rule_name,
        rule_type=rule.rule_type,
        weight=rule.weight,
        parameters=rule.parameters
    )
    db.add(new_rule)
    db.commit()
    db.refresh(new_rule)
    
    return new_rule


# Get Company Scoring Rules
@router.get("/company/{company_id}", response_model=List[ScoringRuleResponse])
def get_company_scoring_rules(company_id: int, db: Session = Depends(get_db)):
    rules = db.query(ScoringRule).filter(
        ScoringRule.company_id == company_id,
        ScoringRule.is_active == True
    ).all()
    return rules


# Get Scoring Rule by ID
@router.get("/{rule_id}", response_model=ScoringRuleResponse)
def get_scoring_rule(rule_id: int, db: Session = Depends(get_db)):
    rule = db.query(ScoringRule).filter(ScoringRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Scoring rule not found")
    return rule


# Update Scoring Rule
@router.put("/{rule_id}", response_model=ScoringRuleResponse)
def update_scoring_rule(rule_id: int, rule: ScoringRuleCreate, db: Session = Depends(get_db)):
    db_rule = db.query(ScoringRule).filter(ScoringRule.id == rule_id).first()
    if not db_rule:
        raise HTTPException(status_code=404, detail="Scoring rule not found")
    
    db_rule.rule_name = rule.rule_name
    db_rule.rule_type = rule.rule_type
    db_rule.weight = rule.weight
    db_rule.parameters = rule.parameters
    db_rule.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(db_rule)
    return db_rule


# Delete Scoring Rule
@router.delete("/{rule_id}")
def delete_scoring_rule(rule_id: int, db: Session = Depends(get_db)):
    rule = db.query(ScoringRule).filter(ScoringRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Scoring rule not found")
    
    rule.is_active = False
    rule.updated_at = datetime.utcnow()
    db.commit()
    
    return {"message": "Scoring rule deleted successfully"}


# Calculate Score with Custom Rules
@router.post("/calculate")
def calculate_score(request: ScoreCalculationRequest):
    scoring = ScoringEngine()
    
    metrics = {
        'shelf_coverage': request.shelf_coverage,
        'visibility_score': request.visibility_score,
        'expected_distribution': request.expected_distribution or {'left': 33, 'center': 34, 'right': 33},
        'actual_distribution': request.actual_distribution or {'left': 0, 'center': 0, 'right': 0},
        'color_matches': request.color_matches or {}
    }
    
    result = scoring.calculate_total_score(metrics, request.custom_weights)
    
    return result


# Get Default Weights
@router.get("/weights/default")
def get_default_weights():
    scoring = ScoringEngine()
    return {
        "default_weights": scoring.default_weights,
        "description": {
            "shelf_coverage": "Weight for shelf coverage score (ideal 70-85%)",
            "product_visibility": "Weight for product visibility and positioning",
            "planogram_compliance": "Weight for planogram compliance",
            "color_match": "Weight for color matching accuracy"
        }
    }


# Calculate Company Custom Score
@router.post("/company/{company_id}/calculate")
def calculate_company_score(
    company_id: int,
    request: ScoreCalculationRequest,
    db: Session = Depends(get_db)
):
    # Get company scoring rules
    rules = db.query(ScoringRule).filter(
        ScoringRule.company_id == company_id,
        ScoringRule.is_active == True
    ).all()
    
    if not rules:
        # Use default weights
        scoring = ScoringEngine()
        weights = scoring.default_weights
    else:
        # Build custom weights from rules
        weights = {}
        total_weight = sum(rule.weight for rule in rules)
        
        for rule in rules:
            normalized_weight = rule.weight / total_weight if total_weight > 0 else 0.25
            weights[rule.rule_type] = normalized_weight
        
        # Fill missing weights with 0
        for key in ['shelf_coverage', 'product_visibility', 'planogram_compliance', 'color_match']:
            if key not in weights:
                weights[key] = 0.0
    
    # Calculate score
    scoring = ScoringEngine()
    metrics = {
        'shelf_coverage': request.shelf_coverage,
        'visibility_score': request.visibility_score,
        'expected_distribution': request.expected_distribution or {'left': 33, 'center': 34, 'right': 33},
        'actual_distribution': request.actual_distribution or {'left': 0, 'center': 0, 'right': 0},
        'color_matches': request.color_matches or {}
    }
    
    result = scoring.calculate_total_score(metrics, weights)
    result['custom_rules_applied'] = len(rules)
    result['custom_weights'] = weights
    
    return result
