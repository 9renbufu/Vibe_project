/**
 * Agent Panel - Agent 面板（右侧面板）
 * 包含: Current Task, Agent Thinking, Design Memory, Design Plan, Version History, AI Evaluation
 */

import React, { useState } from 'react';
import { useAgentStore } from '../../store/agentStore';

export const AgentPanel: React.FC = () => {
  const {
    currentTask,
    phase,
    steps,
    memory,
    plans,
    evaluation,
    isThinking,
    currentStep,
    thinkingLogs,
    preferences,
  } = useAgentStore();

  const [expandedSections, setExpandedSections] = useState<Set<string>>(
    new Set(['task', 'thinking', 'memory', 'plan', 'evaluation'])
  );

  const toggleSection = (id: string) => {
    setExpandedSections((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };

  const selectedPlan = plans.find((p) => p.selected);

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <span style={styles.title}>Agent</span>
        <span style={{
          ...styles.phaseBadge,
          backgroundColor: phase === 'idle' ? '#f3f4f6' : '#eff6ff',
          color: phase === 'idle' ? '#6b7280' : '#3b82f6',
        }}>
          {phase}
        </span>
      </div>

      <div style={styles.scrollArea}>
        {/* Current Task */}
        <Section
          id="task"
          title="Current Task"
          icon=" "
          expanded={expandedSections.has('task')}
          onToggle={() => toggleSection('task')}
        >
          {currentTask ? (
            <div style={styles.taskContent}>
              <p style={styles.taskText}>{currentTask}</p>
              <div style={styles.stepsGrid}>
                {steps.map((step) => (
                  <div
                    key={step.id}
                    style={{
                      ...styles.stepItem,
                      ...(step.status === 'running' ? styles.stepRunning : {}),
                      ...(step.status === 'completed' ? styles.stepCompleted : {}),
                      ...(step.status === 'error' ? styles.stepError : {}),
                    }}
                  >
                    <span style={styles.stepIcon}>{step.icon}</span>
                    <span style={styles.stepName}>{step.name}</span>
                    <span style={styles.stepStatus}>
                      {step.status === 'running' && (
                        <span style={styles.spinnerSmall} />
                      )}
                      {step.status === 'completed' && ''}
                      {step.status === 'error' && ''}
                      {step.status === 'pending' && ''}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div style={styles.emptySection}>
              <span style={styles.emptyText}>No active task</span>
            </div>
          )}
        </Section>

        {/* Agent Thinking */}
        <Section
          id="thinking"
          title="Agent Thinking"
          icon=" "
          expanded={expandedSections.has('thinking')}
          onToggle={() => toggleSection('thinking')}
          badge={isThinking ? 'Thinking...' : undefined}
          badgeColor={isThinking ? '#f59e0b' : undefined}
        >
          {thinkingLogs.length > 0 ? (
            <div style={styles.thinkingContent}>
              {isThinking && (
                <div style={styles.thinkingAnimation}>
                  <span style={styles.thinkingDot}> </span>
                  <span style={styles.thinkingText}>
                    {currentStep || 'Processing...'}
                  </span>
                </div>
              )}
              <div style={styles.thinkingLogs}>
                {thinkingLogs.slice(-10).reverse().map((log, index) => (
                  <div key={index} style={styles.thinkingLogItem}>
                    <div style={styles.thinkingLogHeader}>
                      <span style={styles.thinkingLogAgent}>
                        {log.agent.replace('Agent', '')}
                      </span>
                      <span style={styles.thinkingLogTime}>
                        {new Date(log.timestamp).toLocaleTimeString()}
                      </span>
                    </div>
                    <pre style={styles.thinkingLogContent}>
                      {log.content}
                    </pre>
                  </div>
                ))}
              </div>
            </div>
          ) : isThinking ? (
            <div style={styles.thinkingContent}>
              <div style={styles.thinkingAnimation}>
                <span style={styles.thinkingDot}> </span>
                <span style={styles.thinkingText}>
                  {currentStep || 'Analyzing your request...'}
                </span>
              </div>
              <div style={styles.thinkingSteps}>
                {steps
                  .filter((s) => s.status === 'running' || s.status === 'completed')
                  .map((s) => (
                    <div key={s.id} style={styles.thinkingStep}>
                      <span>{s.status === 'completed' ? '✅' : '⏳'}</span>
                      <span>{s.name}</span>
                      {s.output && (
                        <span style={styles.stepOutput}>{s.output}</span>
                      )}
                    </div>
                  ))}
              </div>
            </div>
          ) : (
            <div style={styles.emptySection}>
              <span style={styles.emptyText}>Agent is idle</span>
            </div>
          )}
        </Section>

        {/* Design Memory */}
        <Section
          id="memory"
          title="Design Memory"
          icon=" "
          expanded={expandedSections.has('memory')}
          onToggle={() => toggleSection('memory')}
        >
          <div style={styles.memoryContent}>
            {/* 长期偏好 */}
            {preferences && (
              <div style={styles.preferenceSection}>
                <span style={styles.preferenceTitle}>Long-term Preferences</span>
                <MemoryField label="Favorite Style" value={preferences.favorite_style || ''} />
                <MemoryField label="Industry" value={preferences.industry || ''} />
                {Array.isArray(preferences.favorite_styles) && preferences.favorite_styles.length > 0 && (
                  <div style={styles.memoryField}>
                    <span style={styles.memoryLabel}>Style History</span>
                    <div style={styles.keywordChips}>
                      {preferences.favorite_styles.map((s, i) => (
                        <span key={i} style={styles.keywordChip}>{s}</span>
                      ))}
                    </div>
                  </div>
                )}
                {Array.isArray(preferences.favorite_colors) && preferences.favorite_colors.length > 0 && (
                  <div style={styles.memoryField}>
                    <span style={styles.memoryLabel}>Color Preferences</span>
                    <div style={styles.colorChips}>
                      {preferences.favorite_colors.map((c, i) => (
                        <span
                          key={i}
                          style={{
                            ...styles.colorChip,
                            backgroundColor: c,
                          }}
                        />
                      ))}
                    </div>
                  </div>
                )}
                <div style={styles.statsRow}>
                  <div style={styles.statItem}>
                    <span style={styles.statValue}>{preferences.total_designs || 0}</span>
                    <span style={styles.statLabel}>Designs</span>
                  </div>
                  <div style={styles.statItem}>
                    <span style={styles.statValue}>{preferences.average_score || 0}</span>
                    <span style={styles.statLabel}>Avg Score</span>
                  </div>
                </div>
              </div>
            )}

            {/* 当前会话记忆 */}
            <div style={styles.preferenceSection}>
              <span style={styles.preferenceTitle}>Current Session</span>
              <MemoryField label="Style" value={memory.style || ''} />
              <MemoryField label="Mood" value={memory.mood || ''} />
              <MemoryField label="Industry" value={memory.industry || ''} />
              {Array.isArray(memory.colors) && memory.colors.length > 0 && (
                <div style={styles.memoryField}>
                  <span style={styles.memoryLabel}>Colors</span>
                  <div style={styles.colorChips}>
                    {memory.colors.map((c, i) => (
                      <span
                        key={i}
                        style={{
                          ...styles.colorChip,
                          backgroundColor: c,
                        }}
                      />
                    ))}
                  </div>
                </div>
              )}
              {Array.isArray(memory.keywords) && memory.keywords.length > 0 && (
                <div style={styles.memoryField}>
                  <span style={styles.memoryLabel}>Keywords</span>
                  <div style={styles.keywordChips}>
                    {memory.keywords.map((k, i) => (
                      <span key={i} style={styles.keywordChip}>{k}</span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </Section>

        {/* Design Plan */}
        <Section
          id="plan"
          title="Design Plan"
          icon=" "
          expanded={expandedSections.has('plan')}
          onToggle={() => toggleSection('plan')}
        >
          {selectedPlan ? (
            <div style={styles.planContent}>
              <h4 style={styles.planName}>{selectedPlan.name}</h4>
              <p style={styles.planDesc}>{selectedPlan.description}</p>
              {selectedPlan.elements.length > 0 && (
                <div style={styles.planElements}>
                  <span style={styles.planLabel}>Elements:</span>
                  {selectedPlan.elements.map((el, i) => (
                    <span key={i} style={styles.planElement}>{el}</span>
                  ))}
                </div>
              )}
              {selectedPlan.score !== undefined && (
                <div style={styles.planScore}>
                  <span style={styles.planLabel}>Score:</span>
                  <div style={styles.scoreBar}>
                    <div
                      style={{
                        ...styles.scoreFill,
                        width: `${selectedPlan.score}%`,
                      }}
                    />
                  </div>
                  <span style={styles.scoreValue}>{selectedPlan.score}</span>
                </div>
              )}
            </div>
          ) : plans.length > 0 ? (
            <div style={styles.planList}>
              {plans.map((p) => (
                <div
                  key={p.id}
                  style={styles.planItem}
                  onClick={() => useAgentStore.getState().selectPlan(p.id)}
                >
                  <span style={styles.planItemName}>{p.name}</span>
                  <span style={styles.planItemDesc}>
                    {p.description.slice(0, 50)}...
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <div style={styles.emptySection}>
              <span style={styles.emptyText}>No plans yet</span>
            </div>
          )}
        </Section>

        {/* AI Evaluation */}
        <Section
          id="evaluation"
          title="AI Evaluation"
          icon=" "
          expanded={expandedSections.has('evaluation')}
          onToggle={() => toggleSection('evaluation')}
        >
          {evaluation ? (
            <div style={styles.evalContent}>
              <div style={styles.evalOverall}>
                <span style={styles.evalScore}>{evaluation.overall}</span>
                <span style={styles.evalLabel}>Overall</span>
              </div>
              <div style={styles.evalBars}>
                <EvalBar label="Brand" value={evaluation.brandConsistency} />
                <EvalBar label="Creative" value={evaluation.creativity} />
                <EvalBar label="Commercial" value={evaluation.commercialValue} />
                <EvalBar label="Aesthetics" value={evaluation.aesthetics} />
              </div>
              {evaluation.feedback && (
                <p style={styles.evalFeedback}>{evaluation.feedback}</p>
              )}
            </div>
          ) : (
            <div style={styles.emptySection}>
              <span style={styles.emptyText}>No evaluation yet</span>
            </div>
          )}
        </Section>
      </div>
    </div>
  );
};

// --- Sub-components ---

interface SectionProps {
  id: string;
  title: string;
  icon: string;
  expanded: boolean;
  onToggle: () => void;
  badge?: string;
  badgeColor?: string;
  children: React.ReactNode;
}

const Section: React.FC<SectionProps> = ({
  title,
  icon,
  expanded,
  onToggle,
  badge,
  badgeColor,
  children,
}) => (
  <div style={styles.section}>
    <div style={styles.sectionHeader} onClick={onToggle}>
      <div style={styles.sectionLeft}>
        <span style={styles.sectionIcon}>{icon}</span>
        <span style={styles.sectionTitle}>{title}</span>
        {badge && (
          <span
            style={{
              ...styles.sectionBadge,
              backgroundColor: badgeColor ? `${badgeColor}20` : '#f3f4f6',
              color: badgeColor || '#6b7280',
            }}
          >
            {badge}
          </span>
        )}
      </div>
      <span style={styles.sectionArrow}>{expanded ? '' : ''}</span>
    </div>
    {expanded && <div style={styles.sectionBody}>{children}</div>}
  </div>
);

interface MemoryFieldProps {
  label: string;
  value: string;
}

const MemoryField: React.FC<MemoryFieldProps> = ({ label, value }) => {
  if (!value) return null;
  return (
    <div style={styles.memoryField}>
      <span style={styles.memoryLabel}>{label}</span>
      <span style={styles.memoryValue}>{value}</span>
    </div>
  );
};

interface EvalBarProps {
  label: string;
  value: number;
}

const EvalBar: React.FC<EvalBarProps> = ({ label, value }) => (
  <div style={styles.evalBarRow}>
    <span style={styles.evalBarLabel}>{label}</span>
    <div style={styles.evalBarTrack}>
      <div
        style={{
          ...styles.evalBarFill,
          width: `${value}%`,
          backgroundColor:
            value >= 80 ? '#10b981' : value >= 60 ? '#f59e0b' : '#ef4444',
        }}
      />
    </div>
    <span style={styles.evalBarValue}>{value}</span>
  </div>
);

const styles: Record<string, React.CSSProperties> = {
  container: {
    display: 'flex',
    flexDirection: 'column',
    height: '100%',
    backgroundColor: '#ffffff',
    borderLeft: '1px solid #e5e7eb',
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '12px 16px',
    borderBottom: '1px solid #e5e7eb',
    backgroundColor: '#fafafa',
  },
  title: {
    fontSize: '14px',
    fontWeight: '600',
    color: '#111827',
  },
  phaseBadge: {
    fontSize: '10px',
    padding: '2px 8px',
    borderRadius: '10px',
    fontWeight: '500',
  },
  scrollArea: {
    flex: 1,
    overflowY: 'auto',
  },
  section: {
    borderBottom: '1px solid #f3f4f6',
  },
  sectionHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '10px 16px',
    cursor: 'pointer',
  },
  sectionLeft: {
    display: 'flex',
    alignItems: 'center',
    gap: '6px',
  },
  sectionIcon: {
    fontSize: '12px',
  },
  sectionTitle: {
    fontSize: '12px',
    fontWeight: '600',
    color: '#374151',
  },
  sectionBadge: {
    fontSize: '9px',
    padding: '1px 6px',
    borderRadius: '8px',
    fontWeight: '500',
  },
  sectionArrow: {
    fontSize: '10px',
    color: '#9ca3af',
  },
  sectionBody: {
    padding: '0 16px 12px',
  },
  emptySection: {
    padding: '12px 0',
    textAlign: 'center',
  },
  emptyText: {
    fontSize: '11px',
    color: '#9ca3af',
  },
  // Task
  taskContent: {},
  taskText: {
    margin: '0 0 10px 0',
    fontSize: '12px',
    color: '#374151',
    lineHeight: '1.5',
  },
  stepsGrid: {
    display: 'flex',
    flexDirection: 'column',
    gap: '4px',
  },
  stepItem: {
    display: 'flex',
    alignItems: 'center',
    gap: '6px',
    padding: '4px 8px',
    borderRadius: '4px',
    backgroundColor: '#f9fafb',
    fontSize: '11px',
  },
  stepRunning: {
    backgroundColor: '#eff6ff',
    border: '1px solid #bfdbfe',
  },
  stepCompleted: {
    backgroundColor: '#f0fdf4',
  },
  stepError: {
    backgroundColor: '#fef2f2',
  },
  stepIcon: {
    fontSize: '10px',
  },
  stepName: {
    flex: 1,
    color: '#374151',
    fontWeight: '500',
  },
  stepStatus: {
    fontSize: '10px',
  },
  spinnerSmall: {
    display: 'inline-block',
    width: '10px',
    height: '10px',
    border: '2px solid #e5e7eb',
    borderTopColor: '#3b82f6',
    borderRadius: '50%',
    animation: 'spin 1s linear infinite',
  },
  // Thinking
  thinkingContent: {},
  thinkingAnimation: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    padding: '8px',
    backgroundColor: '#fffbeb',
    borderRadius: '6px',
    marginBottom: '8px',
  },
  thinkingDot: {
    fontSize: '14px',
    animation: 'pulse 1.5s infinite',
  },
  thinkingText: {
    fontSize: '12px',
    color: '#92400e',
    fontWeight: '500',
  },
  thinkingSteps: {
    display: 'flex',
    flexDirection: 'column',
    gap: '4px',
  },
  thinkingStep: {
    display: 'flex',
    alignItems: 'center',
    gap: '6px',
    fontSize: '11px',
    color: '#6b7280',
    padding: '3px 0',
  },
  stepOutput: {
    fontSize: '10px',
    color: '#9ca3af',
    marginLeft: 'auto',
  },
  thinkingLogs: {
    display: 'flex',
    flexDirection: 'column',
    gap: '8px',
    maxHeight: '300px',
    overflowY: 'auto',
  },
  thinkingLogItem: {
    padding: '8px',
    backgroundColor: '#f9fafb',
    borderRadius: '6px',
    border: '1px solid #e5e7eb',
  },
  thinkingLogHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '4px',
  },
  thinkingLogAgent: {
    fontSize: '10px',
    fontWeight: '600',
    color: '#6366f1',
    backgroundColor: '#eff6ff',
    padding: '1px 6px',
    borderRadius: '4px',
  },
  thinkingLogTime: {
    fontSize: '9px',
    color: '#9ca3af',
  },
  thinkingLogContent: {
    margin: 0,
    fontSize: '10px',
    color: '#374151',
    lineHeight: '1.5',
    whiteSpace: 'pre-wrap',
    wordBreak: 'break-word',
    fontFamily: 'monospace',
  },
  // Memory
  memoryContent: {
    display: 'flex',
    flexDirection: 'column',
    gap: '12px',
  },
  preferenceSection: {
    display: 'flex',
    flexDirection: 'column',
    gap: '6px',
    padding: '8px',
    backgroundColor: '#f9fafb',
    borderRadius: '6px',
  },
  preferenceTitle: {
    fontSize: '10px',
    fontWeight: '600',
    color: '#6366f1',
    textTransform: 'uppercase',
    letterSpacing: '0.5px',
    marginBottom: '4px',
  },
  statsRow: {
    display: 'flex',
    gap: '12px',
    marginTop: '4px',
  },
  statItem: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    padding: '6px 12px',
    backgroundColor: '#fff',
    borderRadius: '4px',
    flex: 1,
  },
  statValue: {
    fontSize: '16px',
    fontWeight: '600',
    color: '#6366f1',
  },
  statLabel: {
    fontSize: '9px',
    color: '#9ca3af',
  },
  memoryField: {
    display: 'flex',
    flexDirection: 'column',
    gap: '2px',
  },
  memoryLabel: {
    fontSize: '10px',
    fontWeight: '600',
    color: '#9ca3af',
    textTransform: 'uppercase',
    letterSpacing: '0.5px',
  },
  memoryValue: {
    fontSize: '12px',
    color: '#374151',
  },
  colorChips: {
    display: 'flex',
    gap: '4px',
    flexWrap: 'wrap',
  },
  colorChip: {
    width: '16px',
    height: '16px',
    borderRadius: '3px',
    border: '1px solid rgba(0,0,0,0.1)',
  },
  keywordChips: {
    display: 'flex',
    gap: '4px',
    flexWrap: 'wrap',
  },
  keywordChip: {
    fontSize: '10px',
    padding: '2px 6px',
    backgroundColor: '#f3f4f6',
    borderRadius: '4px',
    color: '#6b7280',
  },
  // Plan
  planContent: {},
  planName: {
    margin: '0 0 4px 0',
    fontSize: '13px',
    fontWeight: '600',
    color: '#111827',
  },
  planDesc: {
    margin: '0 0 8px 0',
    fontSize: '11px',
    color: '#6b7280',
    lineHeight: '1.5',
  },
  planElements: {
    display: 'flex',
    flexWrap: 'wrap',
    gap: '4px',
    marginBottom: '8px',
  },
  planLabel: {
    fontSize: '10px',
    fontWeight: '600',
    color: '#9ca3af',
    marginRight: '4px',
  },
  planElement: {
    fontSize: '10px',
    padding: '2px 6px',
    backgroundColor: '#eff6ff',
    borderRadius: '4px',
    color: '#3b82f6',
  },
  planScore: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
  },
  scoreBar: {
    flex: 1,
    height: '4px',
    backgroundColor: '#e5e7eb',
    borderRadius: '2px',
    overflow: 'hidden',
  },
  scoreFill: {
    height: '100%',
    backgroundColor: '#6366f1',
    borderRadius: '2px',
    transition: 'width 0.3s',
  },
  scoreValue: {
    fontSize: '12px',
    fontWeight: '600',
    color: '#6366f1',
  },
  planList: {
    display: 'flex',
    flexDirection: 'column',
    gap: '4px',
  },
  planItem: {
    padding: '8px',
    borderRadius: '6px',
    border: '1px solid #e5e7eb',
    cursor: 'pointer',
  },
  planItemName: {
    fontSize: '12px',
    fontWeight: '500',
    color: '#111827',
    display: 'block',
    marginBottom: '2px',
  },
  planItemDesc: {
    fontSize: '10px',
    color: '#9ca3af',
  },
  // Evaluation
  evalContent: {},
  evalOverall: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    padding: '12px',
    backgroundColor: '#f9fafb',
    borderRadius: '8px',
    marginBottom: '12px',
  },
  evalScore: {
    fontSize: '28px',
    fontWeight: '700',
    color: '#6366f1',
  },
  evalLabel: {
    fontSize: '10px',
    color: '#9ca3af',
    fontWeight: '500',
  },
  evalBars: {
    display: 'flex',
    flexDirection: 'column',
    gap: '6px',
    marginBottom: '10px',
  },
  evalBarRow: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
  },
  evalBarLabel: {
    fontSize: '10px',
    color: '#6b7280',
    width: '60px',
    flexShrink: 0,
  },
  evalBarTrack: {
    flex: 1,
    height: '4px',
    backgroundColor: '#e5e7eb',
    borderRadius: '2px',
    overflow: 'hidden',
  },
  evalBarFill: {
    height: '100%',
    borderRadius: '2px',
    transition: 'width 0.3s',
  },
  evalBarValue: {
    fontSize: '10px',
    fontWeight: '600',
    color: '#374151',
    width: '24px',
    textAlign: 'right',
  },
  evalFeedback: {
    margin: 0,
    fontSize: '11px',
    color: '#6b7280',
    lineHeight: '1.5',
    padding: '8px',
    backgroundColor: '#f9fafb',
    borderRadius: '6px',
  },
};
