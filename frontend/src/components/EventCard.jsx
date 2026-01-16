import CompletenessIndicator from './CompletenessIndicator'

const formatDate = (dateString) => {
    if (!dateString) return null
    try {
        const date = new Date(dateString)
        return date.toLocaleDateString('en-US', {
            weekday: 'short',
            month: 'short',
            day: 'numeric',
            year: 'numeric'
        })
    } catch {
        return null
    }
}

const formatBadge = {
    'online': { class: 'badge-online', icon: '🌐', label: 'Online' },
    'in-person': { class: 'badge-in-person', icon: '📍', label: 'In-Person' },
    'hybrid': { class: 'badge-hybrid', icon: '🔄', label: 'Hybrid' },
}

const typeIcons = {
    'conference': '🎤',
    'workshop': '🛠️',
    'lecture': '🎓',
    'seminar': '📖',
    'webinar': '💻',
    'course': '📚',
    'other': '📌',
}

export default function EventCard({ event }) {
    const dateFormatted = formatDate(event.start_date)
    const format = formatBadge[event.format] || formatBadge['online']
    const typeIcon = typeIcons[event.event_type] || typeIcons['other']

    return (
        <article className="glass-card rounded-2xl p-5 hover-lift h-full flex flex-col">
            {/* Header */}
            <div className="flex items-start justify-between gap-2 mb-3">
                <div className="flex items-center gap-2">
                    <span className={`badge ${format.class}`}>
                        {format.icon} {format.label}
                    </span>
                    <span className="text-lg" title={event.event_type}>
                        {typeIcon}
                    </span>
                </div>
                <CompletenessIndicator
                    score={event.completeness_score}
                    missingFields={event.missing_fields}
                />
            </div>

            {/* Title */}
            <h3 className="font-semibold text-gray-900 line-clamp-2 mb-2 flex-grow-0">
                {event.title || 'Untitled Event'}
            </h3>

            {/* Date */}
            {dateFormatted && (
                <div className="flex items-center gap-2 text-sm text-gray-600 mb-2">
                    <svg className="w-4 h-4 text-primary-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                    </svg>
                    {dateFormatted}
                </div>
            )}

            {/* Location */}
            {(event.location?.city || event.location?.venue) && (
                <div className="flex items-center gap-2 text-sm text-gray-600 mb-2">
                    <svg className="w-4 h-4 text-accent-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                    </svg>
                    <span className="truncate">
                        {event.location.venue || event.location.city}
                        {event.location.city && event.location.country && `, ${event.location.country}`}
                    </span>
                </div>
            )}

            {/* Organizer */}
            {event.organizer?.name && event.organizer.name !== 'Unknown' && (
                <div className="flex items-center gap-2 text-sm text-gray-500 mb-3">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                    </svg>
                    {event.organizer.name}
                </div>
            )}

            {/* Description preview */}
            {event.description && (
                <p className="text-sm text-gray-600 line-clamp-2 mb-4 flex-grow">
                    {event.description}
                </p>
            )}

            {/* Fee */}
            {event.registration?.fee && (
                <div className="text-sm font-medium text-primary-600 mb-3">
                    💰 {event.registration.fee}
                </div>
            )}

            {/* Actions */}
            <div className="mt-auto pt-3 border-t border-slate-100">
                {event.registration?.url ? (
                    <a
                        href={event.registration.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="block w-full text-center px-4 py-2.5 text-white font-medium rounded-lg transition-all hover:opacity-90"
                        style={{ background: 'linear-gradient(135deg, #1e3a5f 0%, #2d5a87 100%)' }}
                    >
                        View Details
                    </a>
                ) : (
                    <button
                        disabled
                        className="block w-full text-center px-4 py-2.5 bg-slate-100 text-slate-400 font-medium rounded-lg cursor-not-allowed"
                    >
                        No link available
                    </button>
                )}
            </div>
        </article>
    )
}
