import os

from flask import Flask, request, session
from flask_cors import CORS

from compiler.lexer import lexer
from compiler.parser import parser
from compiler.symbol_table_builder import SymbolTableBuilder
from compiler.tac import TACGenerator
from compiler.basic_blocks import BasicBlockBuilder
from compiler.cfg import CFGBuilder
from compiler.data_flow import ReachingDefinitions
from compiler.def_use import DefUseChain
from compiler.explanation import ExplanationEngine
from compiler.change_analyzer import ChangeAnalyzer
from compiler.impact_analyzer import ImpactAnalyzer

from database import init_database
from models import Analysis, db
from auth import auth_bp


app = Flask(__name__)
app.config["SECRET_KEY"] = "codelens-development-secret"

is_production = os.getenv("RENDER", "").lower() == "true"
app.config["SESSION_COOKIE_SECURE"] = is_production
app.config["SESSION_COOKIE_SAMESITE"] = "None" if is_production else "Lax"

CORS(
    app,
    origins=[
        "http://localhost:5173",
        "https://cd-2420030443-team9-code.vercel.app",
    ],
    supports_credentials=True,
)


init_database(app)

app.register_blueprint(auth_bp)

with app.app_context():
    db.create_all()


@app.route("/")
def home():
    return {
        "message": "CodeLens backend is running"
    }


@app.route("/health")
def health():
    return {
        "status": "healthy"
    }


@app.route("/api/analyses", methods=["GET"])
def get_analyses():
    user_id = session.get("user_id")

    if not user_id:
        return {
            "error": "Not authenticated."
        }, 401

    analyses = Analysis.query.filter_by(
        user_id=user_id
    ).order_by(
        Analysis.updated_at.desc()
    ).all()

    return {
        "analyses": [
            {
                "id": analysis.id,
                "name": analysis.name,
                "source_code": analysis.source_code,
                "analysis_result": analysis.analysis_result,
                "created_at": analysis.created_at,
                "updated_at": analysis.updated_at,
            }
            for analysis in analyses
        ]
    }, 200


@app.route("/api/analyze", methods=["POST"])
def analyze_code():
    data = request.get_json()

    if not data or "code" not in data:
        return {
            "error": "Code is required."
        }, 400

    code = data["code"]

    try:
        ast = parser.parse(
            code,
            lexer=lexer,
        )

        if ast is None:
            return {
                "error": "Unable to parse the provided code."
            }, 400

        symbol_builder = SymbolTableBuilder()
        symbol_table = symbol_builder.build(ast)

        tac_generator = TACGenerator()
        tac_instructions = tac_generator.generate(ast)

        block_builder = BasicBlockBuilder()
        basic_blocks = block_builder.build(
            tac_instructions
        )

        cfg_builder = CFGBuilder()
        cfg = cfg_builder.build(
            basic_blocks
        )

        reaching_definitions = ReachingDefinitions(
            basic_blocks,
            cfg,
        )

        data_flow = reaching_definitions.analyze()

        def_use_analyzer = DefUseChain(
            basic_blocks,
            reaching_definitions,
        )

        def_use = def_use_analyzer.analyze()

        explanation_engine = ExplanationEngine()
        explanation = explanation_engine.explain(ast)

        analysis_result = {
            "message": "Analysis completed successfully.",
            "explanation": explanation,
            "ast": ast_to_dict(ast),
            "symbols": symbols_to_dict(
                symbol_table
            ),
            "tac": [
                str(instruction)
                for instruction in tac_instructions
            ],
            "basic_blocks": blocks_to_dict(
                basic_blocks
            ),
            "cfg": cfg_to_dict(cfg),
            "data_flow": data_flow_to_dict(
                data_flow
            ),
            "def_use": def_use_to_dict(
                def_use
            ),
        }

        user_id = session.get("user_id")

        if user_id:
            analysis = Analysis(
                user_id=user_id,
                name=(
                    data.get("name")
                    or "Untitled analysis"
                ).strip(),
                source_code=code,
                analysis_result=analysis_result,
            )

            db.session.add(analysis)
            db.session.commit()

        return analysis_result

    except Exception as error:
        return {
            "error": str(error)
        }, 500


@app.route("/api/impact", methods=["POST"])
def analyze_impact():
    data = request.get_json(silent=True)

    if not data:
        return {
            "error": "Request body is required."
        }, 400

    before_code = data.get("before_code")
    after_code = data.get("after_code")

    if (
        not isinstance(before_code, str)
        or not before_code.strip()
        or not isinstance(after_code, str)
        or not after_code.strip()
    ):
        return {
            "error": "Both before_code and after_code are required."
        }, 400

    try:
        old_ast = parser.parse(
            before_code,
            lexer=lexer,
        )

        new_ast = parser.parse(
            after_code,
            lexer=lexer,
        )

        if old_ast is None:
            return {
                "error": "Unable to parse the old code."
            }, 400

        if new_ast is None:
            return {
                "error": "Unable to parse the new code."
            }, 400

        change_analyzer = ChangeAnalyzer()

        changes = change_analyzer.compare(
            old_ast,
            new_ast,
        )

        # Compile both submitted programs independently.  The comparison
        # therefore cannot accidentally analyze one program twice.
        before_representations = build_compiler_representations(old_ast)
        after_representations = build_compiler_representations(new_ast)

        impact_analyzer = ImpactAnalyzer()

        impacts = impact_analyzer.analyze(
            old_ast,
            new_ast,
            changes,
            after_representations["cfg_object"],
            after_representations["def_use_object"],
            before_representations["cfg_object"],
        )

        return {
            "message": "Change impact analysis completed successfully.",
            "changes": [
                {
                    "type": change.change_type,
                    "description": change.description,
                    "path": change.path,
                }
                for change in changes
            ],
            "impacts": [
                {
                    "impact_type": impact.impact_type,
                    "description": impact.description,
                    "path": impact.path,
                }
                for impact in impacts
            ],
            "boundary_cases": impact_analyzer.boundary_cases,
            "execution": impact_analyzer.execution,
            "representations": {
                "before": before_representations["serialized"],
                "after": after_representations["serialized"],
            },
        }

    except Exception as error:
        return {
            "error": str(error)
        }, 500


def ast_to_dict(node):
    if node is None:
        return None

    if hasattr(
        node,
        "__dataclass_fields__",
    ):
        result = {
            "type": type(node).__name__
        }

        for field_name in (
            node.__dataclass_fields__
        ):
            value = getattr(
                node,
                field_name,
            )

            if (
                field_name == "type"
                and type(node).__name__
                != "Parameter"
            ):
                result["data_type"] = (
                    ast_to_dict(value)
                )
            else:
                result[field_name] = (
                    ast_to_dict(value)
                )

        return result

    if isinstance(node, list):
        return [
            ast_to_dict(item)
            for item in node
        ]

    if isinstance(node, dict):
        return {
            key: ast_to_dict(value)
            for key, value in node.items()
        }

    return node


def symbols_to_dict(symbol_table):
    result = []

    for scope_data in symbol_table.all_scopes:
        scope_name = scope_data["name"]

        for symbol in scope_data[
            "symbols"
        ].values():
            result.append(
                {
                    "name": symbol.name,
                    "type": symbol.symbol_type,
                    "kind": symbol.kind,
                    "scope": scope_name,
                    "line": symbol.line,
                }
            )

    return result


def blocks_to_dict(blocks):
    result = []

    for block in blocks:
        result.append(
            {
                "id": block.id,
                "instructions": [
                    str(instruction)
                    for instruction in block.instructions
                ],
            }
        )

    return result


def cfg_to_dict(cfg):
    nodes = []

    for block_id, node in cfg.nodes.items():
        nodes.append(
            {
                "id": block_id,
                "successors": sorted(
                    node.successors
                ),
                "predecessors": sorted(
                    node.predecessors
                ),
            }
        )

    edges = [
        {
            "from": from_block,
            "to": to_block,
        }
        for from_block, to_block in cfg.get_edges()
    ]

    return {
        "nodes": nodes,
        "edges": edges,
    }


def data_flow_to_dict(data_flow):
    result = {}

    for key in (
        "gen",
        "kill",
        "in",
        "out",
    ):
        result[key] = {}

        for block_id, definitions in data_flow[
            key
        ].items():
            result[key][str(block_id)] = [
                {
                    "variable": definition.variable,
                    "block": definition.block_id,
                    "instruction": definition.instruction_index,
                    "value": definition.value,
                }
                for definition in definitions
            ]

    return result


def def_use_to_dict(def_use):
    result = []

    for definition, uses in def_use.items():
        result.append(
            {
                "definition": {
                    "variable": definition.variable,
                    "block": definition.block_id,
                    "instruction": definition.instruction_index,
                    "value": definition.value,
                },
                "uses": [
                    {
                        "variable": use.variable,
                        "block": use.block_id,
                        "instruction": use.instruction_index,
                        "statement": use.instruction,
                    }
                    for use in sorted(
                        uses,
                        key=lambda item: (
                            item.block_id,
                            item.instruction_index,
                        ),
                    )
                ],
            }
        )

    return result


def build_compiler_representations(ast):
    """Build the compiler artifacts for one side of an impact comparison."""
    symbol_table = SymbolTableBuilder().build(ast)
    tac_instructions = TACGenerator().generate(ast)
    basic_blocks = BasicBlockBuilder().build(tac_instructions)
    cfg = CFGBuilder().build(basic_blocks)
    reaching_definitions = ReachingDefinitions(basic_blocks, cfg)
    data_flow = reaching_definitions.analyze()
    def_use = DefUseChain(basic_blocks, reaching_definitions).analyze()

    return {
        "cfg_object": cfg,
        "def_use_object": def_use,
        "serialized": {
            "ast": ast_to_dict(ast),
            "symbols": symbols_to_dict(symbol_table),
            "tac": [str(instruction) for instruction in tac_instructions],
            "basic_blocks": blocks_to_dict(basic_blocks),
            "cfg": cfg_to_dict(cfg),
            "data_flow": data_flow_to_dict(data_flow),
            "def_use": def_use_to_dict(def_use),
        },
    }


if __name__ == "__main__":
    app.run(
        debug=True,
        port=5000,
    )
