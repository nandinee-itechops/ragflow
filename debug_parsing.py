#!/usr/bin/env python3
"""
RAGFlow Document Parsing Debug Script
=====================================

This script helps monitor and debug document parsing issues in RAGFlow.
It checks task status, identifies stuck documents, and provides insights.
"""

import requests
import json
import time
import sys
from datetime import datetime

class RAGFlowDebugger:
    def __init__(self, base_url="http://localhost:9380", api_key=None):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {api_key}' if api_key else ''
        }
    
    def check_system_status(self):
        """Check if RAGFlow services are running"""
        try:
            response = requests.get(f"{self.base_url}/v1/health", timeout=5)
            print(f"✅ RAGFlow is running (Status: {response.status_code})")
            return True
        except requests.exceptions.RequestException as e:
            print(f"❌ RAGFlow is not accessible: {e}")
            return False
    
    def get_document_status(self, kb_id):
        """Get status of all documents in a knowledge base"""
        try:
            url = f"{self.base_url}/v1/documents/list"
            params = {
                'kb_id': kb_id,
                'page': 0,
                'page_size': 100
            }
            response = requests.post(url, json=params, headers=self.headers)
            
            if response.status_code == 200:
                data = response.json()
                return data.get('data', {}).get('docs', [])
            else:
                print(f"Error getting documents: {response.status_code}")
                return []
        except Exception as e:
            print(f"Error: {e}")
            return []
    
    def analyze_parsing_issues(self, docs):
        """Analyze documents for parsing issues"""
        issues = {
            'stuck': [],
            'failed': [],
            'partial': [],
            'successful': []
        }
        
        for doc in docs:
            run_status = doc.get('run', 'UNKNOWN')
            progress = doc.get('progress', 0)
            progress_msg = doc.get('progress_msg', '')
            doc_name = doc.get('name', 'Unknown')
            
            if 'Canceled' in progress_msg or 'ERROR' in progress_msg:
                issues['failed'].append({
                    'name': doc_name,
                    'status': run_status,
                    'progress': progress,
                    'message': progress_msg
                })
            elif run_status == 'RUNNING' and progress < 1:
                issues['stuck'].append({
                    'name': doc_name,
                    'status': run_status,
                    'progress': progress,
                    'message': progress_msg
                })
            elif progress < 1 and progress > 0:
                issues['partial'].append({
                    'name': doc_name,
                    'status': run_status,
                    'progress': progress,
                    'message': progress_msg
                })
            elif progress >= 1 or run_status == 'DONE':
                issues['successful'].append({
                    'name': doc_name,
                    'status': run_status,
                    'progress': progress
                })
        
        return issues
    
    def print_analysis(self, issues):
        """Print analysis results"""
        print("\n" + "="*60)
        print("📊 DOCUMENT PARSING ANALYSIS")
        print("="*60)
        
        print(f"✅ Successful: {len(issues['successful'])}")
        print(f"⚠️  Partial: {len(issues['partial'])}")
        print(f"🔄 Stuck: {len(issues['stuck'])}")
        print(f"❌ Failed: {len(issues['failed'])}")
        
        if issues['failed']:
            print("\n❌ FAILED DOCUMENTS:")
            for doc in issues['failed']:
                print(f"  - {doc['name']}: {doc['message']}")
        
        if issues['stuck']:
            print("\n🔄 STUCK DOCUMENTS:")
            for doc in issues['stuck']:
                print(f"  - {doc['name']}: {doc['progress']*100:.1f}% - {doc['message']}")
        
        if issues['partial']:
            print("\n⚠️  PARTIALLY PROCESSED DOCUMENTS:")
            for doc in issues['partial']:
                print(f"  - {doc['name']}: {doc['progress']*100:.1f}% - {doc['message']}")
    
    def get_recommendations(self, issues):
        """Provide recommendations based on analysis"""
        recommendations = []
        
        if issues['failed']:
            recommendations.append("🔧 For failed documents:")
            recommendations.append("   - Check if embedding model is accessible")
            recommendations.append("   - Increase timeout values in .env file")
            recommendations.append("   - Verify document format is supported")
        
        if issues['stuck']:
            recommendations.append("🔧 For stuck documents:")
            recommendations.append("   - Restart parsing by clicking the red X in UI")
            recommendations.append("   - Increase MAX_CONCURRENT_TASKS in .env")
            recommendations.append("   - Check system resources (CPU/Memory)")
        
        if len(issues['partial']) > len(issues['successful']):
            recommendations.append("🔧 For high partial failure rate:")
            recommendations.append("   - Increase DOC_BULK_SIZE in .env")
            recommendations.append("   - Increase EMBEDDING_BATCH_SIZE in .env")
            recommendations.append("   - Check network connectivity to embedding service")
        
        return recommendations

def main():
    print("🔍 RAGFlow Document Parsing Debugger")
    print("-" * 40)
    
    debugger = RAGFlowDebugger()
    
    # Check system status
    if not debugger.check_system_status():
        sys.exit(1)
    
    # Get knowledge base ID (you'll need to provide this)
    kb_id = input("Enter Knowledge Base ID to analyze (or press Enter to skip): ").strip()
    
    if not kb_id:
        print("ℹ️  No KB ID provided. Please check your knowledge bases in the RAGFlow UI.")
        print("   You can find the KB ID in the URL when viewing a knowledge base.")
        return
    
    # Get documents and analyze
    print(f"📋 Getting documents for KB: {kb_id}")
    docs = debugger.get_document_status(kb_id)
    
    if not docs:
        print("❌ No documents found or error accessing API")
        return
    
    issues = debugger.analyze_parsing_issues(docs)
    debugger.print_analysis(issues)
    
    # Print recommendations
    recommendations = debugger.get_recommendations(issues)
    if recommendations:
        print("\n💡 RECOMMENDATIONS:")
        for rec in recommendations:
            print(rec)
    
    print("\n" + "="*60)
    print("✅ Analysis complete!")

if __name__ == "__main__":
    main()
