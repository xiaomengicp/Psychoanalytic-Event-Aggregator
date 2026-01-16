import { useState } from 'react'

export default function CompletenessIndicator({ score = 0, missingFields = [] }) {
    const [showTooltip, setShowTooltip] = useState(false)

    // Determine color based on score
    let colorClass, bgClass, label
    if (score >= 80) {
        colorClass = 'completeness-high'
        bgClass = 'bg-green-100'
        label = 'Complete'
    } else if (score >= 50) {
        colorClass = 'completeness-medium'
        bgClass = 'bg-yellow-100'
        label = 'Partial'
    } else {
        colorClass = 'completeness-low'
        bgClass = 'bg-red-100'
        label = 'Incomplete'
    }

    return (
        <div
            className="relative"
            onMouseEnter={() => setShowTooltip(true)}
            onMouseLeave={() => setShowTooltip(false)}
        >
            <div
                className={`flex items-center gap-1.5 px-2 py-1 rounded-lg ${bgClass} cursor-help`}
            >
                {/* Progress ring */}
                <svg className="w-4 h-4" viewBox="0 0 36 36">
                    <path
                        className="stroke-gray-200"
                        strokeWidth="3"
                        fill="none"
                        d="M18 2.0845
              a 15.9155 15.9155 0 0 1 0 31.831
              a 15.9155 15.9155 0 0 1 0 -31.831"
                    />
                    <path
                        className={colorClass.replace('text-', 'stroke-')}
                        strokeWidth="3"
                        strokeLinecap="round"
                        fill="none"
                        strokeDasharray={`${score}, 100`}
                        d="M18 2.0845
              a 15.9155 15.9155 0 0 1 0 31.831
              a 15.9155 15.9155 0 0 1 0 -31.831"
                    />
                </svg>
                <span className={`text-xs font-medium ${colorClass}`}>
                    {score}%
                </span>
            </div>

            {/* Tooltip */}
            {showTooltip && missingFields.length > 0 && (
                <div className="absolute right-0 top-full mt-2 z-50 w-48 p-3 bg-gray-900 text-white text-xs rounded-lg shadow-lg">
                    <div className="font-medium mb-1">{label} Information</div>
                    <div className="text-gray-300">
                        Missing: {missingFields.join(', ')}
                    </div>
                    {/* Arrow */}
                    <div className="absolute -top-1 right-3 w-2 h-2 bg-gray-900 transform rotate-45"></div>
                </div>
            )}
        </div>
    )
}
