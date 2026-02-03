# DORA Metrics Implementation Guide

## Table of Contents

- [Overview](#overview)
- [The Four DORA Metrics](#the-four-dora-metrics)
- [Implementation Strategy](#implementation-strategy)
- [Data Collection](#data-collection)
- [Metrics Calculation](#metrics-calculation)
- [Visualization](#visualization)
- [GitHub Actions Integration](#github-actions-integration)
- [Complete Implementation](#complete-implementation)
- [Analysis and Reporting](#analysis-and-reporting)
- [Continuous Improvement](#continuous-improvement)

---

## Overview

DORA (DevOps Research and Assessment) metrics are four key metrics that indicate the performance of software delivery:

1. **Deployment Frequency** - How often you deploy to production
2. **Lead Time for Changes** - Time from commit to production deployment
3. **Change Failure Rate** - Percentage of deployments causing failures
4. **Time to Restore Service** - Time to recover from a failure

### DORA Performance Levels

| Metric | Elite | High | Medium | Low |
|--------|-------|------|--------|-----|
| **Deployment Frequency** | Multiple per day | Weekly to monthly | Monthly to every 6 months | Less than every 6 months |
| **Lead Time for Changes** | Less than 1 hour | 1 day to 1 week | 1 week to 1 month | 1 to 6 months |
| **Change Failure Rate** | 0-15% | 16-30% | 31-45% | 46-60% |
| **Time to Restore Service** | Less than 1 hour | Less than 1 day | 1 day to 1 week | More than 1 week |

---

## The Four DORA Metrics

### 1. Deployment Frequency

**What it measures**: How often code is successfully deployed to production.

**Why it matters**: Higher frequency indicates better automation, smaller batches, and faster feedback.

**Data needed from our pipeline**:
- Deployment timestamp
- Target environment
- Deployment status (success/failure)
- Branch/version deployed

### 2. Lead Time for Changes

**What it measures**: Time from code commit to running in production.

**Why it matters**: Shorter lead time means faster value delivery to users.

**Data needed from our pipeline**:
- Commit timestamp
- Deployment timestamp
- Environment (to track production only)

### 3. Change Failure Rate

**What it measures**: Percentage of deployments that cause failures requiring remediation.

**Why it matters**: Lower rate indicates better quality and testing.

**Data needed from our pipeline**:
- Total deployments
- Failed deployments (including rollbacks)
- Health check failures
- Rollback triggers

### 4. Time to Restore Service

**What it measures**: Time from incident detection to service restoration.

**Why it matters**: Faster recovery minimizes business impact.

**Data needed from our pipeline**:
- Failure detection timestamp
- Rollback initiation timestamp
- Service restoration timestamp

---

## Implementation Strategy

### Phase 1: Data Collection (Weeks 1-2)

1. Add metrics tracking to workflow
2. Store metrics in a database or data warehouse
3. Set up GitHub API integration

### Phase 2: Metrics Calculation (Week 3)

1. Create calculation scripts
2. Automate metric aggregation
3. Generate daily/weekly reports

### Phase 3: Visualization (Week 4)

1. Create dashboards
2. Set up alerting for degradation
3. Share with stakeholders

---

## Data Collection

### Option 1: GitHub API + Database (Recommended)

Create a centralized metrics collection system:

```python
# scripts/collect-dora-metrics.py
import os
import json
from datetime import datetime
import psycopg2
from github import Github

class DORAMetricsCollector:
    def __init__(self, github_token, db_connection_string):
        self.gh = Github(github_token)
        self.conn = psycopg2.connect(db_connection_string)
        
    def collect_deployment_metrics(self, repo_name, workflow_run_id):
        """Collect metrics for a deployment"""
        repo = self.gh.get_repo(repo_name)
        workflow_run = repo.get_workflow_run(workflow_run_id)
        
        # Extract deployment data
        metrics = {
            'workflow_run_id': workflow_run_id,
            'repository': repo_name,
            'deployment_time': workflow_run.created_at,
            'completion_time': workflow_run.updated_at,
            'status': workflow_run.conclusion,  # success, failure, cancelled
            'environment': self._get_environment(workflow_run),
            'version': self._get_version(workflow_run),
            'branch': workflow_run.head_branch,
            'commit_sha': workflow_run.head_sha,
            'triggered_by': workflow_run.actor.login,
        }
        
        # Get commit data for lead time
        commit = repo.get_commit(workflow_run.head_sha)
        metrics['commit_time'] = commit.commit.author.date
        metrics['lead_time_minutes'] = (
            metrics['completion_time'] - metrics['commit_time']
        ).total_seconds() / 60
        
        # Check if deployment failed or was rolled back
        metrics['failure'] = self._check_failure(workflow_run)
        metrics['rollback'] = self._check_rollback(workflow_run)
        
        # Store in database
        self._store_metrics(metrics)
        
        return metrics
    
    def _get_environment(self, workflow_run):
        """Extract environment from workflow run"""
        # Parse workflow inputs or job names
        for job in workflow_run.jobs():
            if 'environment' in job.name.lower():
                return job.name.split('-')[-1]
        return 'unknown'
    
    def _get_version(self, workflow_run):
        """Extract version from artifacts or logs"""
        artifacts = workflow_run.get_artifacts()
        for artifact in artifacts:
            if 'version' in artifact.name.lower():
                # Download and parse version
                pass
        return 'unknown'
    
    def _check_failure(self, workflow_run):
        """Check if deployment failed"""
        return workflow_run.conclusion in ['failure', 'cancelled']
    
    def _check_rollback(self, workflow_run):
        """Check if rollback occurred"""
        for job in workflow_run.jobs():
            if 'rollback' in job.name.lower() and job.conclusion == 'success':
                return True
        return False
    
    def _store_metrics(self, metrics):
        """Store metrics in PostgreSQL"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO dora_metrics 
            (workflow_run_id, repository, deployment_time, completion_time,
             status, environment, version, branch, commit_sha, commit_time,
             lead_time_minutes, failure, rollback, triggered_by)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (workflow_run_id) DO UPDATE SET
                completion_time = EXCLUDED.completion_time,
                status = EXCLUDED.status,
                failure = EXCLUDED.failure,
                rollback = EXCLUDED.rollback
        """, (
            metrics['workflow_run_id'],
            metrics['repository'],
            metrics['deployment_time'],
            metrics['completion_time'],
            metrics['status'],
            metrics['environment'],
            metrics['version'],
            metrics['branch'],
            metrics['commit_sha'],
            metrics['commit_time'],
            metrics['lead_time_minutes'],
            metrics['failure'],
            metrics['rollback'],
            metrics['triggered_by']
        ))
        self.conn.commit()
        cursor.close()

# Usage
if __name__ == '__main__':
    collector = DORAMetricsCollector(
        github_token=os.getenv('GITHUB_TOKEN'),
        db_connection_string=os.getenv('DATABASE_URL')
    )
    
    collector.collect_deployment_metrics(
        repo_name=os.getenv('GITHUB_REPOSITORY'),
        workflow_run_id=os.getenv('GITHUB_RUN_ID')
    )
```

### Database Schema

```sql
-- Create DORA metrics table
CREATE TABLE dora_metrics (
    id SERIAL PRIMARY KEY,
    workflow_run_id BIGINT UNIQUE NOT NULL,
    repository VARCHAR(255) NOT NULL,
    deployment_time TIMESTAMP NOT NULL,
    completion_time TIMESTAMP,
    status VARCHAR(50),
    environment VARCHAR(50),
    version VARCHAR(100),
    branch VARCHAR(255),
    commit_sha VARCHAR(40),
    commit_time TIMESTAMP,
    lead_time_minutes INTEGER,
    failure BOOLEAN DEFAULT FALSE,
    rollback BOOLEAN DEFAULT FALSE,
    triggered_by VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for faster queries
CREATE INDEX idx_deployment_time ON dora_metrics(deployment_time);
CREATE INDEX idx_environment ON dora_metrics(environment);
CREATE INDEX idx_repository ON dora_metrics(repository);
CREATE INDEX idx_status ON dora_metrics(status);

-- Create incident tracking table
CREATE TABLE incidents (
    id SERIAL PRIMARY KEY,
    incident_id VARCHAR(100) UNIQUE NOT NULL,
    repository VARCHAR(255) NOT NULL,
    environment VARCHAR(50),
    detected_at TIMESTAMP NOT NULL,
    resolved_at TIMESTAMP,
    resolution_method VARCHAR(50), -- 'rollback', 'hotfix', 'manual'
    related_deployment_id INTEGER REFERENCES dora_metrics(id),
    severity VARCHAR(20), -- 'critical', 'high', 'medium', 'low'
    mttr_minutes INTEGER, -- Mean Time To Restore
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_detected_at ON incidents(detected_at);
CREATE INDEX idx_environment_incidents ON incidents(environment);
```

### Option 2: GitHub Actions Artifacts

Store metrics as workflow artifacts:

```yaml
# Add to workflow
- name: Record DORA Metrics
  if: always()
  run: |
    cat > dora-metrics.json << EOF
    {
      "workflow_run_id": "${{ github.run_id }}",
      "repository": "${{ github.repository }}",
      "deployment_time": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
      "environment": "${{ inputs.environment }}",
      "version": "${{ steps.set_version.outputs.version }}",
      "branch": "${{ github.ref_name }}",
      "commit_sha": "${{ github.sha }}",
      "status": "${{ job.status }}",
      "deployment_status": "${{ steps.deployment.outputs.status }}",
      "health_status": "${{ steps.health_check.outputs.status }}",
      "rollback_occurred": "${{ needs.rollback.result == 'success' }}"
    }
    EOF
    
- name: Upload DORA Metrics
  if: always()
  uses: actions/upload-artifact@v4
  with:
    name: dora-metrics-${{ github.run_id }}
    path: dora-metrics.json
    retention-days: 90
```

### Option 3: Direct Database Insert from Workflow

Add to the workflow:

```yaml
- name: Record Metrics to Database
  if: always()
  env:
    DATABASE_URL: ${{ secrets.METRICS_DATABASE_URL }}
  run: |
    python3 << 'PYTHON_SCRIPT'
    import os
    import json
    from datetime import datetime
    import psycopg2
    
    conn = psycopg2.connect(os.getenv('DATABASE_URL'))
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO dora_metrics 
        (workflow_run_id, repository, deployment_time, environment, 
         version, branch, commit_sha, status, failure, rollback)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        '${{ github.run_id }}',
        '${{ github.repository }}',
        datetime.utcnow(),
        '${{ inputs.environment }}',
        '${{ steps.set_version.outputs.version }}',
        '${{ github.ref_name }}',
        '${{ github.sha }}',
        '${{ job.status }}',
        '${{ steps.deployment.outputs.status }}' == 'failed',
        '${{ needs.rollback.result }}' == 'success'
    ))
    
    conn.commit()
    cursor.close()
    conn.close()
    PYTHON_SCRIPT
```

---

## Metrics Calculation

Create scripts to calculate DORA metrics:

```python
# scripts/calculate-dora-metrics.py
import psycopg2
from datetime import datetime, timedelta
import pandas as pd

class DORAMetricsCalculator:
    def __init__(self, db_connection_string):
        self.conn = psycopg2.connect(db_connection_string)
    
    def deployment_frequency(self, environment='production', days=30):
        """
        Calculate deployment frequency
        Returns: deployments per day
        """
        query = """
            SELECT 
                DATE(deployment_time) as date,
                COUNT(*) as deployments
            FROM dora_metrics
            WHERE 
                environment = %s
                AND deployment_time >= NOW() - INTERVAL '%s days'
                AND status = 'success'
            GROUP BY DATE(deployment_time)
            ORDER BY date
        """
        
        df = pd.read_sql(query, self.conn, params=(environment, days))
        
        if df.empty:
            return {
                'deployments_per_day': 0,
                'total_deployments': 0,
                'days_with_deployments': 0,
                'level': 'Low'
            }
        
        total_deployments = df['deployments'].sum()
        deployments_per_day = total_deployments / days
        days_with_deployments = len(df)
        
        # Classify performance level
        if deployments_per_day >= 1:
            level = 'Elite'
        elif deployments_per_day >= 1/7:  # Weekly
            level = 'High'
        elif deployments_per_day >= 1/30:  # Monthly
            level = 'Medium'
        else:
            level = 'Low'
        
        return {
            'deployments_per_day': round(deployments_per_day, 2),
            'total_deployments': int(total_deployments),
            'days_with_deployments': days_with_deployments,
            'level': level,
            'data': df.to_dict('records')
        }
    
    def lead_time_for_changes(self, environment='production', days=30):
        """
        Calculate lead time for changes
        Returns: median and p95 lead time in hours
        """
        query = """
            SELECT 
                lead_time_minutes,
                deployment_time
            FROM dora_metrics
            WHERE 
                environment = %s
                AND deployment_time >= NOW() - INTERVAL '%s days'
                AND status = 'success'
                AND lead_time_minutes IS NOT NULL
            ORDER BY deployment_time
        """
        
        df = pd.read_sql(query, self.conn, params=(environment, days))
        
        if df.empty:
            return {
                'median_hours': None,
                'p95_hours': None,
                'level': 'Low'
            }
        
        median_minutes = df['lead_time_minutes'].median()
        p95_minutes = df['lead_time_minutes'].quantile(0.95)
        
        median_hours = median_minutes / 60
        p95_hours = p95_minutes / 60
        
        # Classify performance level (based on median)
        if median_hours < 1:
            level = 'Elite'
        elif median_hours < 24:
            level = 'High'
        elif median_hours < 168:  # 1 week
            level = 'Medium'
        else:
            level = 'Low'
        
        return {
            'median_hours': round(median_hours, 2),
            'p95_hours': round(p95_hours, 2),
            'median_minutes': round(median_minutes, 2),
            'p95_minutes': round(p95_minutes, 2),
            'level': level,
            'sample_size': len(df)
        }
    
    def change_failure_rate(self, environment='production', days=30):
        """
        Calculate change failure rate
        Returns: percentage of failed deployments
        """
        query = """
            SELECT 
                COUNT(*) as total_deployments,
                SUM(CASE WHEN failure = TRUE OR rollback = TRUE THEN 1 ELSE 0 END) as failed_deployments
            FROM dora_metrics
            WHERE 
                environment = %s
                AND deployment_time >= NOW() - INTERVAL '%s days'
        """
        
        cursor = self.conn.cursor()
        cursor.execute(query, (environment, days))
        result = cursor.fetchone()
        cursor.close()
        
        total = result[0] or 0
        failed = result[1] or 0
        
        if total == 0:
            failure_rate = 0
        else:
            failure_rate = (failed / total) * 100
        
        # Classify performance level
        if failure_rate <= 15:
            level = 'Elite'
        elif failure_rate <= 30:
            level = 'High'
        elif failure_rate <= 45:
            level = 'Medium'
        else:
            level = 'Low'
        
        return {
            'failure_rate_percent': round(failure_rate, 2),
            'total_deployments': total,
            'failed_deployments': failed,
            'level': level
        }
    
    def time_to_restore_service(self, environment='production', days=30):
        """
        Calculate mean time to restore service
        Returns: median and p95 MTTR in hours
        """
        query = """
            SELECT 
                mttr_minutes,
                detected_at,
                resolved_at,
                resolution_method
            FROM incidents
            WHERE 
                environment = %s
                AND detected_at >= NOW() - INTERVAL '%s days'
                AND resolved_at IS NOT NULL
            ORDER BY detected_at
        """
        
        df = pd.read_sql(query, self.conn, params=(environment, days))
        
        if df.empty:
            return {
                'median_hours': None,
                'p95_hours': None,
                'mean_hours': None,
                'level': 'Elite',  # No incidents is good!
                'incident_count': 0
            }
        
        median_minutes = df['mttr_minutes'].median()
        p95_minutes = df['mttr_minutes'].quantile(0.95)
        mean_minutes = df['mttr_minutes'].mean()
        
        median_hours = median_minutes / 60
        p95_hours = p95_minutes / 60
        mean_hours = mean_minutes / 60
        
        # Classify performance level (based on median)
        if median_hours < 1:
            level = 'Elite'
        elif median_hours < 24:
            level = 'High'
        elif median_hours < 168:  # 1 week
            level = 'Medium'
        else:
            level = 'Low'
        
        return {
            'median_hours': round(median_hours, 2),
            'p95_hours': round(p95_hours, 2),
            'mean_hours': round(mean_hours, 2),
            'median_minutes': round(median_minutes, 2),
            'level': level,
            'incident_count': len(df),
            'by_resolution_method': df.groupby('resolution_method')['mttr_minutes'].mean().to_dict()
        }
    
    def generate_report(self, environment='production', days=30):
        """Generate comprehensive DORA metrics report"""
        report = {
            'report_date': datetime.utcnow().isoformat(),
            'environment': environment,
            'period_days': days,
            'metrics': {
                'deployment_frequency': self.deployment_frequency(environment, days),
                'lead_time': self.lead_time_for_changes(environment, days),
                'change_failure_rate': self.change_failure_rate(environment, days),
                'time_to_restore': self.time_to_restore_service(environment, days)
            }
        }
        
        # Calculate overall performance level
        levels = [
            report['metrics']['deployment_frequency']['level'],
            report['metrics']['lead_time']['level'],
            report['metrics']['change_failure_rate']['level'],
            report['metrics']['time_to_restore']['level']
        ]
        
        level_scores = {'Elite': 4, 'High': 3, 'Medium': 2, 'Low': 1}
        avg_score = sum(level_scores[l] for l in levels) / len(levels)
        
        if avg_score >= 3.5:
            overall = 'Elite'
        elif avg_score >= 2.5:
            overall = 'High'
        elif avg_score >= 1.5:
            overall = 'Medium'
        else:
            overall = 'Low'
        
        report['overall_performance'] = overall
        
        return report

# Usage
if __name__ == '__main__':
    import json
    import sys
    
    calculator = DORAMetricsCalculator(os.getenv('DATABASE_URL'))
    
    # Generate report for production (last 30 days)
    report = calculator.generate_report('production', 30)
    
    # Print report
    print(json.dumps(report, indent=2))
    
    # Also generate for other environments
    for env in ['development', 'staging']:
        env_report = calculator.generate_report(env, 30)
        with open(f'dora-metrics-{env}.json', 'w') as f:
            json.dump(env_report, f, indent=2)
```

---

## Visualization

### Option 1: Grafana Dashboard

Create a Grafana dashboard with PostgreSQL as data source:

```json
{
  "dashboard": {
    "title": "DORA Metrics Dashboard",
    "panels": [
      {
        "title": "Deployment Frequency",
        "targets": [
          {
            "rawSql": "SELECT deployment_time as time, COUNT(*) as deployments FROM dora_metrics WHERE environment = 'production' AND $__timeFilter(deployment_time) GROUP BY time_bucket('1 day', deployment_time) ORDER BY 1"
          }
        ],
        "type": "graph"
      },
      {
        "title": "Lead Time for Changes",
        "targets": [
          {
            "rawSql": "SELECT deployment_time as time, PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY lead_time_minutes) as median_lead_time FROM dora_metrics WHERE environment = 'production' AND $__timeFilter(deployment_time) GROUP BY time_bucket('1 day', deployment_time) ORDER BY 1"
          }
        ],
        "type": "graph"
      },
      {
        "title": "Change Failure Rate",
        "targets": [
          {
            "rawSql": "SELECT deployment_time as time, (SUM(CASE WHEN failure OR rollback THEN 1 ELSE 0 END)::float / COUNT(*)::float * 100) as failure_rate FROM dora_metrics WHERE environment = 'production' AND $__timeFilter(deployment_time) GROUP BY time_bucket('1 week', deployment_time) ORDER BY 1"
          }
        ],
        "type": "graph"
      },
      {
        "title": "Mean Time to Restore",
        "targets": [
          {
            "rawSql": "SELECT detected_at as time, AVG(mttr_minutes) as mttr FROM incidents WHERE environment = 'production' AND $__timeFilter(detected_at) GROUP BY time_bucket('1 week', detected_at) ORDER BY 1"
          }
        ],
        "type": "graph"
      }
    ]
  }
}
```

### Option 2: Custom Web Dashboard

```python
# dashboard/app.py
from flask import Flask, render_template, jsonify
import os
from calculate_dora_metrics import DORAMetricsCalculator

app = Flask(__name__)
calculator = DORAMetricsCalculator(os.getenv('DATABASE_URL'))

@app.route('/')
def dashboard():
    return render_template('dashboard.html')

@app.route('/api/metrics/<environment>')
def get_metrics(environment):
    days = request.args.get('days', 30, type=int)
    report = calculator.generate_report(environment, days)
    return jsonify(report)

@app.route('/api/metrics/<environment>/trend')
def get_trend(environment):
    """Get metrics over time for trend analysis"""
    days = request.args.get('days', 90, type=int)
    
    # Calculate metrics for each week
    trends = []
    for week in range(days // 7):
        week_report = calculator.generate_report(
            environment, 
            7,
            offset_days=week * 7
        )
        trends.append(week_report)
    
    return jsonify(trends)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
```

```html
<!-- dashboard/templates/dashboard.html -->
<!DOCTYPE html>
<html>
<head>
    <title>DORA Metrics Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .metric-card {
            border: 1px solid #ddd;
            padding: 20px;
            margin: 10px;
            border-radius: 8px;
            display: inline-block;
            width: 300px;
        }
        .metric-value { font-size: 2em; font-weight: bold; }
        .metric-level { 
            padding: 5px 10px;
            border-radius: 4px;
            display: inline-block;
            margin-top: 10px;
        }
        .level-Elite { background-color: #28a745; color: white; }
        .level-High { background-color: #17a2b8; color: white; }
        .level-Medium { background-color: #ffc107; color: black; }
        .level-Low { background-color: #dc3545; color: white; }
    </style>
</head>
<body>
    <h1>DORA Metrics Dashboard</h1>
    
    <div id="metrics-container"></div>
    
    <div style="margin-top: 40px;">
        <canvas id="deployment-frequency-chart"></canvas>
    </div>
    
    <script>
        async function loadMetrics() {
            const response = await fetch('/api/metrics/production');
            const data = await response.json();
            
            const container = document.getElementById('metrics-container');
            container.innerHTML = `
                <div class="metric-card">
                    <h3>Deployment Frequency</h3>
                    <div class="metric-value">${data.metrics.deployment_frequency.deployments_per_day}</div>
                    <div>per day</div>
                    <div class="metric-level level-${data.metrics.deployment_frequency.level}">
                        ${data.metrics.deployment_frequency.level}
                    </div>
                </div>
                
                <div class="metric-card">
                    <h3>Lead Time for Changes</h3>
                    <div class="metric-value">${data.metrics.lead_time.median_hours}h</div>
                    <div>median</div>
                    <div class="metric-level level-${data.metrics.lead_time.level}">
                        ${data.metrics.lead_time.level}
                    </div>
                </div>
                
                <div class="metric-card">
                    <h3>Change Failure Rate</h3>
                    <div class="metric-value">${data.metrics.change_failure_rate.failure_rate_percent}%</div>
                    <div>${data.metrics.change_failure_rate.failed_deployments} / ${data.metrics.change_failure_rate.total_deployments} deployments</div>
                    <div class="metric-level level-${data.metrics.change_failure_rate.level}">
                        ${data.metrics.change_failure_rate.level}
                    </div>
                </div>
                
                <div class="metric-card">
                    <h3>Time to Restore Service</h3>
                    <div class="metric-value">${data.metrics.time_to_restore.median_hours || 'N/A'}h</div>
                    <div>median (${data.metrics.time_to_restore.incident_count} incidents)</div>
                    <div class="metric-level level-${data.metrics.time_to_restore.level}">
                        ${data.metrics.time_to_restore.level}
                    </div>
                </div>
            `;
        }
        
        loadMetrics();
    </script>
</body>
</html>
```

---

## GitHub Actions Integration

### Add Metrics Collection to Workflow

```yaml
# Add new job to workflow
jobs:
  # ... existing jobs ...
  
  collect-metrics:
    needs: [deploy, health-check]
    if: always()
    runs-on: [self-hosted]
    environment: ${{ inputs.environment }}
    
    steps:
      - name: Checkout metrics repo
        uses: actions/checkout@v4
        with:
          repository: your-org/dora-metrics
          token: ${{ secrets.METRICS_REPO_TOKEN }}
          path: metrics
      
      - name: Collect deployment metrics
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          DATABASE_URL: ${{ secrets.METRICS_DATABASE_URL }}
        run: |
          python metrics/scripts/collect-dora-metrics.py
      
      - name: Record incident if deployment failed
        if: |
          needs.deploy.result == 'failure' || 
          needs.health-check.outputs.health_status == 'unhealthy'
        env:
          DATABASE_URL: ${{ secrets.METRICS_DATABASE_URL }}
        run: |
          python << 'PYTHON'
          import psycopg2
          import os
          from datetime import datetime
          
          conn = psycopg2.connect(os.getenv('DATABASE_URL'))
          cursor = conn.cursor()
          
          cursor.execute("""
              INSERT INTO incidents 
              (incident_id, repository, environment, detected_at, severity)
              VALUES (%s, %s, %s, %s, %s)
          """, (
              '${{ github.run_id }}-incident',
              '${{ github.repository }}',
              '${{ inputs.environment }}',
              datetime.utcnow(),
              'high'
          ))
          
          conn.commit()
          cursor.close()
          conn.close()
          PYTHON
      
      - name: Update incident resolution
        if: needs.rollback.result == 'success'
        env:
          DATABASE_URL: ${{ secrets.METRICS_DATABASE_URL }}
        run: |
          python << 'PYTHON'
          import psycopg2
          import os
          from datetime import datetime
          
          conn = psycopg2.connect(os.getenv('DATABASE_URL'))
          cursor = conn.cursor()
          
          cursor.execute("""
              UPDATE incidents 
              SET 
                  resolved_at = %s,
                  resolution_method = 'rollback',
                  mttr_minutes = EXTRACT(EPOCH FROM (%s - detected_at)) / 60
              WHERE incident_id = %s
          """, (
              datetime.utcnow(),
              datetime.utcnow(),
              '${{ github.run_id }}-incident'
          ))
          
          conn.commit()
          cursor.close()
          conn.close()
          PYTHON
```

### Automated Metrics Reporting

Create a scheduled workflow:

```yaml
# .github/workflows/dora-metrics-report.yml
name: Generate DORA Metrics Report

on:
  schedule:
    - cron: '0 9 * * 1'  # Every Monday at 9 AM
  workflow_dispatch:

jobs:
  generate-report:
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout
        uses: actions/checkout@v4
      
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install psycopg2-binary pandas matplotlib seaborn
      
      - name: Generate metrics report
        env:
          DATABASE_URL: ${{ secrets.METRICS_DATABASE_URL }}
        run: |
          python scripts/calculate-dora-metrics.py > dora-report.json
      
      - name: Create visualization
        run: |
          python scripts/visualize-metrics.py
      
      - name: Upload report
        uses: actions/upload-artifact@v4
        with:
          name: dora-metrics-report
          path: |
            dora-report.json
            dora-metrics-*.png
      
      - name: Send to Slack
        uses: slackapi/slack-github-action@v1
        with:
          payload: |
            {
              "text": "Weekly DORA Metrics Report",
              "attachments": [
                {
                  "color": "good",
                  "fields": [
                    {
                      "title": "Report Available",
                      "value": "Check the workflow artifacts for detailed metrics"
                    }
                  ]
                }
              ]
            }
        env:
          SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}
```

---

## Complete Implementation

### Step-by-Step Implementation Guide

#### Step 1: Set Up Database

```bash
# Create PostgreSQL database
createdb dora_metrics

# Run schema creation
psql dora_metrics < schema.sql
```

#### Step 2: Configure Secrets

Add to GitHub repository secrets:
- `METRICS_DATABASE_URL` - PostgreSQL connection string
- `METRICS_REPO_TOKEN` - Token for metrics repository access

#### Step 3: Deploy Metrics Collection

```bash
# Create metrics repository
gh repo create your-org/dora-metrics --private

# Add collection scripts
cd dora-metrics
mkdir -p scripts
cp collect-dora-metrics.py scripts/
cp calculate-dora-metrics.py scripts/
git add .
git commit -m "Add DORA metrics collection"
git push
```

#### Step 4: Update Pipeline Workflow

Add the `collect-metrics` job to your workflow (see above).

#### Step 5: Set Up Dashboard

```bash
# Option A: Grafana
docker run -d -p 3000:3000 --name=grafana grafana/grafana

# Option B: Custom dashboard
cd dashboard
pip install -r requirements.txt
python app.py
```

#### Step 6: Test Collection

Trigger a deployment and verify metrics are collected:

```sql
-- Check collected metrics
SELECT * FROM dora_metrics ORDER BY deployment_time DESC LIMIT 10;
```

#### Step 7: Generate First Report

```bash
python scripts/calculate-dora-metrics.py
```

---

## Analysis and Reporting

### Weekly Report Template

```python
# scripts/generate-weekly-report.py
from calculate_dora_metrics import DORAMetricsCalculator
from datetime import datetime, timedelta
import json

calculator = DORAMetricsCalculator(os.getenv('DATABASE_URL'))

# Generate reports for all environments
report = {
    'week_ending': datetime.utcnow().isoformat(),
    'environments': {}
}

for env in ['production', 'staging', 'development']:
    env_metrics = calculator.generate_report(env, 7)  # Last 7 days
    report['environments'][env] = env_metrics

# Generate markdown report
markdown = f"""
# DORA Metrics Weekly Report
**Week Ending**: {report['week_ending'][:10]}

## Production Environment

### Deployment Frequency
- **{report['environments']['production']['metrics']['deployment_frequency']['deployments_per_day']}** deployments per day
- **Level**: {report['environments']['production']['metrics']['deployment_frequency']['level']}
- Total deployments: {report['environments']['production']['metrics']['deployment_frequency']['total_deployments']}

### Lead Time for Changes
- **Median**: {report['environments']['production']['metrics']['lead_time']['median_hours']} hours
- **95th percentile**: {report['environments']['production']['metrics']['lead_time']['p95_hours']} hours
- **Level**: {report['environments']['production']['metrics']['lead_time']['level']}

### Change Failure Rate
- **{report['environments']['production']['metrics']['change_failure_rate']['failure_rate_percent']}%**
- **Level**: {report['environments']['production']['metrics']['change_failure_rate']['level']}
- Failed: {report['environments']['production']['metrics']['change_failure_rate']['failed_deployments']} / {report['environments']['production']['metrics']['change_failure_rate']['total_deployments']}

### Time to Restore Service
- **Median**: {report['environments']['production']['metrics']['time_to_restore']['median_hours']} hours
- **Level**: {report['environments']['production']['metrics']['time_to_restore']['level']}
- Incidents: {report['environments']['production']['metrics']['time_to_restore']['incident_count']}

## Overall Performance: {report['environments']['production']['overall_performance']}

---

## Trend Analysis
[Include graphs and trend analysis here]

## Recommendations
[Add specific recommendations based on metrics]
"""

print(markdown)

# Save to file
with open('weekly-report.md', 'w') as f:
    f.write(markdown)
```

---

## Continuous Improvement

### Setting Goals

Based on current performance, set incremental goals:

```yaml
# goals.yml
quarterly_goals:
  Q1_2024:
    deployment_frequency:
      current: 0.5  # per day
      target: 1.0
      actions:
        - Automate more tests
        - Reduce PR review time
        - Implement feature flags
    
    lead_time:
      current: 48  # hours
      target: 24
      actions:
        - Optimize CI/CD pipeline
        - Parallelize build steps
        - Reduce manual approvals
    
    change_failure_rate:
      current: 25  # percent
      target: 15
      actions:
        - Improve test coverage
        - Add integration tests
        - Implement canary deployments
    
    mttr:
      current: 4  # hours
      target: 1
      actions:
        - Improve monitoring
        - Automate rollback triggers
        - Create runbooks
```

### Monthly Review Process

1. **Generate metrics report**
2. **Team review meeting**:
   - Celebrate improvements
   - Identify bottlenecks
   - Discuss incidents
3. **Action items**:
   - Assign ownership
   - Set deadlines
   - Track progress
4. **Update goals** if needed

---

## Quick Reference

### Queries for Common Analyses

```sql
-- Top 5 slowest deployments
SELECT 
    version,
    branch,
    lead_time_minutes / 60.0 as lead_time_hours,
    deployment_time
FROM dora_metrics
WHERE environment = 'production'
ORDER BY lead_time_minutes DESC
LIMIT 5;

-- Deployment frequency by day of week
SELECT 
    TO_CHAR(deployment_time, 'Day') as day_of_week,
    COUNT(*) as deployments
FROM dora_metrics
WHERE 
    environment = 'production'
    AND deployment_time >= NOW() - INTERVAL '90 days'
GROUP BY TO_CHAR(deployment_time, 'Day'), EXTRACT(DOW FROM deployment_time)
ORDER BY EXTRACT(DOW FROM deployment_time);

-- Failure rate by branch type
SELECT 
    CASE 
        WHEN branch LIKE 'feature/%' THEN 'feature'
        WHEN branch LIKE 'hotfix/%' THEN 'hotfix'
        WHEN branch LIKE 'bugfix/%' THEN 'bugfix'
        ELSE branch
    END as branch_type,
    COUNT(*) as total,
    SUM(CASE WHEN failure OR rollback THEN 1 ELSE 0 END) as failures,
    ROUND(SUM(CASE WHEN failure OR rollback THEN 1 ELSE 0 END)::numeric / COUNT(*) * 100, 2) as failure_rate
FROM dora_metrics
WHERE environment = 'production'
GROUP BY branch_type
ORDER BY failure_rate DESC;

-- Deployments by hour of day
SELECT 
    EXTRACT(HOUR FROM deployment_time) as hour,
    COUNT(*) as deployments
FROM dora_metrics
WHERE environment = 'production'
GROUP BY hour
ORDER BY hour;
```

---

## Summary Checklist

- [ ] Set up PostgreSQL database with schema
- [ ] Add metrics collection to workflow
- [ ] Configure GitHub secrets for database access
- [ ] Deploy metrics collection scripts
- [ ] Set up dashboard (Grafana or custom)
- [ ] Create automated reporting workflow
- [ ] Test metrics collection with a deployment
- [ ] Generate first weekly report
- [ ] Share dashboard with team
- [ ] Schedule monthly review meetings
- [ ] Set quarterly improvement goals

---

**Last Updated**: January 30, 2024  
**Version**: 1.0.0