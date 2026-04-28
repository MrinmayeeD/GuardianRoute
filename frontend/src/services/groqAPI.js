/**
 * Groq API Service
 * Handles all Groq API calls for AI-powered features like FIR generation and reporting
 */

const GROQ_API_KEY = import.meta.env.VITE_GROQ_API_KEY;
const GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions";

export const callGroqAPI = async (prompt, model = "llama-3.1-8b-instant") => {
  if (!GROQ_API_KEY) {
    return "Error: GROQ_API_KEY is not configured. Please set VITE_GROQ_API_KEY in your .env file.";
  }

  try {
    const response = await fetch(GROQ_API_URL, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${GROQ_API_KEY}`,
      },
      body: JSON.stringify({
        model: model,
        messages: [
          {
            role: "user",
            content: prompt,
          },
        ],
        temperature: 0.7,
        max_tokens: 2000,
      }),
    });

    const data = await response.json();

    if (!response.ok) {
      console.error("Groq API Error:", data);
      return `Error: ${data.error?.message || `HTTP ${response.status}`}`;
    }

    return data.choices?.[0]?.message?.content || "No response generated.";
  } catch (error) {
    console.error("Groq API Exception:", error);
    return `Error: ${error.message || "AI generation failed."}`;
  }
};

/**
 * Generate FIR based on incident details
 */
export const generateFIR = async (firName, firDescription, firLocation, firTime) => {
  const prompt = `
Generate a formal Indian police FIR (First Information Report) based on the following details:

**Complainant Name:** ${firName}
**Incident Description:** ${firDescription}
**Location:** ${firLocation}
**Date & Time:** ${firTime}

Please format this as an official FIR with proper sections including:
1. FIR Number (use a placeholder like FIR/2024/XXXXX)
2. Station Name and Code
3. Complainant Details
4. Details of Accused (if known)
5. Particulars of Offense
6. Details of Witnesses
7. Description of Offense
8. Statement of Complainant
9. Officer's Remarks

Make it professional and appropriate for official police records.
`;

  return await callGroqAPI(prompt);
};

/**
 * Generate AI report summary from incidents
 */
export const generateIncidentReport = async (incidents) => {
  if (!incidents || incidents.length === 0) {
    return "No incidents to generate report from.";
  }

  const incidentSummary = incidents
    .slice(0, 10) // Limit to 10 incidents for prompt size
    .map(
      (incident) =>
        `Type: ${incident.type}, Severity: ${incident.severity}, Status: ${incident.status}, Location: ${incident.location}`
    )
    .join("\n");

  const prompt = `
Generate an official safety authority report summarizing the following reported incidents:

${incidentSummary}

Please provide:
1. Executive Summary
2. Incident Statistics
3. Key Findings
4. Risk Assessment
5. Recommendations
6. Conclusion

Format it as a professional report suitable for local authorities.
`;

  return await callGroqAPI(prompt);
};

/**
 * Generate safety insights from tourist data and incidents
 */
export const generateSafetyInsights = async (touristCount, activeIncidents, averageSafetyScore) => {
  const prompt = `
Analyze the following safety data and provide actionable insights:

**Tourist Count:** ${touristCount}
**Active Incidents:** ${activeIncidents}
**Average Safety Score:** ${averageSafetyScore.toFixed(2)}/100

Please provide:
1. Overall Safety Assessment
2. Areas of Concern
3. Positive Safety Indicators
4. Immediate Actions Required
5. Long-term Safety Improvements

Keep the response concise and professional.
`;

  return await callGroqAPI(prompt);
};
