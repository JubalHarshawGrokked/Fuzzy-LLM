import json
from rewriter import rewrite_text, decide_reasoning_mode
from decider import inference
from openai import OpenAI
from prompts import FINAL_PROMPT, EVALUATION_PROMPT
import os
from pydantic import BaseModel
from typing import Literal
import matplotlib.pyplot as plt

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class EvaluationResult(BaseModel):
    score: Literal[0, 1]  # Restricted to exactly 0 or 1


def process_single_case(case_id, raw_context, raw_question, expected_answer):
    """Process a single test case and return the evaluation score."""
    
    print(f"\n{'='*60}")
    print(f"Processing Case ID: {case_id}")
    print(f"{'='*60}")
    
    # Step 1: Rewrite text
    clean_context = rewrite_text(raw_context)
    clean_question = rewrite_text(raw_question)
    
    # Step 2: Decide reasoning mode
    mode = decide_reasoning_mode(clean_context, clean_question)
    print(f"[INFO] Reasoning mode: {mode}")
    
    # Step 3: Do Inference
    program_result = inference(mode, clean_question, clean_context)
    print(f"[INFO] Tool execution result: {program_result}")
    
    # Step 4: Summarize results in natural language
    user_text = (
        f"We did inference from the context:\n{clean_context}\n"
        f"and the question:\n{clean_question}\n"
        f"Reasoning mode used was \n{mode}\n"
        f"The tool returned the following result:\n{program_result}\n"
        f"Please summarize it in clear natural language for the user."
    )
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": FINAL_PROMPT},
            {"role": "user", "content": user_text}
        ],
        temperature=0.7
    )
    
    final_summary = response.choices[0].message.content.strip()
    print(f"\n[GENERATED SUMMARY]:\n{final_summary}")
    print(f"\n[EXPECTED ANSWER]:\n{expected_answer}")
    
    # Step 5: Evaluate the result
    eval_text = (
        f"Generated Summary:\n{final_summary}\n\n"
        f"Expected Answer:\n{expected_answer}"
    )
    
    eval_response = client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": EVALUATION_PROMPT},
            {"role": "user", "content": eval_text}
        ],
        response_format=EvaluationResult,
        temperature=0.9
    )
    
    score = eval_response.choices[0].message.parsed.score
    print(f"\n[EVALUATION SCORE]: {score} ({'PASS' if score == 1 else 'FAIL'})")
    
    return {
        "id": case_id,
        "generated_summary": final_summary,
        "expected_answer": expected_answer,
        "score": score
    }


def generate_visualization(results, output_path):
    """Generate a visualization of success vs failure."""
    
    passed = sum(1 for r in results if r["score"] == 1)
    failed = len(results) - passed
    
    # Create figure with two subplots
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    
    # Subplot 1: Pie chart
    colors = ['#4CAF50', '#F44336']  # Green for pass, red for fail
    labels = ['Passed', 'Failed']
    sizes = [passed, failed]
    explode = (0.05, 0.05)
    
    ax1.pie(sizes, explode=explode, labels=labels, colors=colors, 
            autopct='%1.1f%%', startangle=90, textprops={'fontsize': 12, 'weight': 'bold'})
    ax1.set_title('Test Results Distribution', fontsize=14, weight='bold', pad=20)
    
    # Subplot 2: Bar chart
    categories = ['Passed', 'Failed']
    counts = [passed, failed]
    bars = ax2.bar(categories, counts, color=colors, alpha=0.8, edgecolor='black', linewidth=1.5)
    
    ax2.set_ylabel('Number of Cases', fontsize=12, weight='bold')
    ax2.set_title('Success vs Failure Count', fontsize=14, weight='bold', pad=20)
    ax2.set_ylim(0, max(counts) * 1.2 if max(counts) > 0 else 10)
    ax2.grid(axis='y', alpha=0.3, linestyle='--')
    
    # Add value labels on bars
    for bar in bars:
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height,
                f'{int(height)}',
                ha='center', va='bottom', fontsize=12, weight='bold')
    
    # Add overall statistics as text
    total = len(results)
    accuracy = (passed / total * 100) if total > 0 else 0
    stats_text = f'Total: {total} | Accuracy: {accuracy:.2f}%'
    fig.text(0.5, 0.02, stats_text, ha='center', fontsize=12, 
             weight='bold', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    plt.tight_layout(rect=[0, 0.05, 1, 1])
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"\nVisualization saved to: {output_path}")
    plt.close()


def evaluate_from_json(json_file_path):
    """
    Load test cases from JSON file and evaluate each one.
    
    Expected JSON format:
    [
        {
            "id": "test_1",
            "raw_context": "Context text...",
            "raw_question": "Question text...",
            "answer": "Expected answer..."
        },
        ...
    ]
    """
    
    # Load test cases
    with open(json_file_path, 'r', encoding='utf-8') as f:
        test_cases = json.load(f)
    
    print(f"Loaded {len(test_cases)} test cases from {json_file_path}")
    
    results = []
    
    # Process each test case
    for case in test_cases:
        try:
            result = process_single_case(
                case_id=case["id"],
                raw_context=case["raw_context"],
                raw_question=case["raw_question"],
                expected_answer=case["answer"]
            )
            results.append(result)
        except Exception as e:
            print(f"\n[ERROR] Failed to process case {case['id']}: {str(e)}")
            results.append({
                "id": case["id"],
                "generated_summary": None,
                "expected_answer": case["answer"],
                "score": 0,
                "error": str(e)
            })
    
    # Calculate overall statistics
    total = len(results)
    passed = sum(1 for r in results if r["score"] == 1)
    failed = total - passed
    accuracy = (passed / total * 100) if total > 0 else 0
    
    print("\n" + "="*60)
    print("EVALUATION SUMMARY")
    print("="*60)
    print(f"Total cases: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Accuracy: {accuracy:.2f}%")
    print("="*60)
    
    # Save results to JSON file
    output_file = json_file_path.replace('.json', '_results.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            "summary": {
                "total": total,
                "passed": passed,
                "failed": failed,
                "accuracy": accuracy
            },
            "results": results
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\nResults saved to: {output_file}")
    
    # Generate visualization
    graph_file = json_file_path.replace('.json', '_visualization.png')
    generate_visualization(results, graph_file)
    
    return results


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python evaluate_results.py <path_to_test_cases.json>")
        sys.exit(1)
    
    json_file = sys.argv[1]
    evaluate_from_json(json_file)