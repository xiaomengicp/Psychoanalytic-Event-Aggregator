import { useState } from 'react'

export default function SubmitEventModal({ isOpen, onClose }) {
    const [formData, setFormData] = useState({
        title: '',
        date: '',
        url: '',
        organization: '',
        description: '',
        format: 'online',
        eventType: 'workshop'
    })
    const [submitted, setSubmitted] = useState(false)

    if (!isOpen) return null

    const handleChange = (e) => {
        const { name, value } = e.target
        setFormData(prev => ({ ...prev, [name]: value }))
    }

    const handleSubmit = (e) => {
        e.preventDefault()
        setSubmitted(true)
    }

    const generateJson = () => {
        return JSON.stringify({
            title: formData.title,
            start_date: formData.date,
            registration: { url: formData.url },
            organizer: { name: formData.organization },
            description: formData.description,
            format: formData.format,
            event_type: formData.eventType
        }, null, 2)
    }

    const handleCopy = () => {
        navigator.clipboard.writeText(generateJson())
    }

    const handleClose = () => {
        setFormData({
            title: '',
            date: '',
            url: '',
            organization: '',
            description: '',
            format: 'online',
            eventType: 'workshop'
        })
        setSubmitted(false)
        onClose()
    }

    return (
        <div className="fixed inset-0 bg-black/40 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            <div className="glass-card rounded-2xl max-w-lg w-full max-h-[90vh] overflow-y-auto animate-fade-in">
                <div className="p-6">
                    <div className="flex items-center justify-between mb-6">
                        <h2 className="text-xl font-semibold gradient-text">Submit an Event</h2>
                        <button
                            onClick={handleClose}
                            className="p-2 hover:bg-slate-100 rounded-lg transition-colors"
                        >
                            <svg className="w-5 h-5 text-slate-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                            </svg>
                        </button>
                    </div>

                    {!submitted ? (
                        <form onSubmit={handleSubmit} className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-slate-700 mb-1">Event Title *</label>
                                <input
                                    type="text"
                                    name="title"
                                    value={formData.title}
                                    onChange={handleChange}
                                    required
                                    className="w-full px-3 py-2 rounded-lg border border-slate-200 bg-white/80 focus:bg-white"
                                    placeholder="e.g., Annual Psychoanalytic Conference 2026"
                                />
                            </div>

                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-sm font-medium text-slate-700 mb-1">Date *</label>
                                    <input
                                        type="date"
                                        name="date"
                                        value={formData.date}
                                        onChange={handleChange}
                                        required
                                        className="w-full px-3 py-2 rounded-lg border border-slate-200 bg-white/80"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-slate-700 mb-1">Format</label>
                                    <select
                                        name="format"
                                        value={formData.format}
                                        onChange={handleChange}
                                        className="w-full px-3 py-2 rounded-lg border border-slate-200 bg-white/80"
                                    >
                                        <option value="online">Online</option>
                                        <option value="in-person">In-Person</option>
                                        <option value="hybrid">Hybrid</option>
                                    </select>
                                </div>
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-slate-700 mb-1">Event URL *</label>
                                <input
                                    type="url"
                                    name="url"
                                    value={formData.url}
                                    onChange={handleChange}
                                    required
                                    className="w-full px-3 py-2 rounded-lg border border-slate-200 bg-white/80"
                                    placeholder="https://..."
                                />
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-slate-700 mb-1">Organization</label>
                                <input
                                    type="text"
                                    name="organization"
                                    value={formData.organization}
                                    onChange={handleChange}
                                    className="w-full px-3 py-2 rounded-lg border border-slate-200 bg-white/80"
                                    placeholder="e.g., International Psychoanalytical Association"
                                />
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-slate-700 mb-1">Description</label>
                                <textarea
                                    name="description"
                                    value={formData.description}
                                    onChange={handleChange}
                                    rows={3}
                                    className="w-full px-3 py-2 rounded-lg border border-slate-200 bg-white/80 resize-none"
                                    placeholder="Brief event description..."
                                />
                            </div>

                            <button
                                type="submit"
                                className="w-full py-2.5 text-white font-medium rounded-lg transition-all hover:opacity-90"
                                style={{ background: 'linear-gradient(135deg, #1e3a5f 0%, #2d5a87 100%)' }}
                            >
                                Generate Submission
                            </button>
                        </form>
                    ) : (
                        <div className="space-y-4">
                            <p className="text-sm text-slate-600">
                                Please copy this information and submit via GitHub Issue or email for review:
                            </p>
                            <div className="bg-slate-50 rounded-lg p-4 border border-slate-200">
                                <pre className="text-xs text-slate-700 overflow-x-auto whitespace-pre-wrap">
                                    {generateJson()}
                                </pre>
                            </div>
                            <div className="flex gap-3">
                                <button
                                    onClick={handleCopy}
                                    className="flex-1 px-4 py-2 bg-slate-100 hover:bg-slate-200 rounded-lg text-sm font-medium transition-colors"
                                >
                                    Copy JSON
                                </button>
                                <a
                                    href={`mailto:events@example.com?subject=New Event Submission&body=${encodeURIComponent(generateJson())}`}
                                    className="flex-1 px-4 py-2 text-center text-sm font-medium text-white rounded-lg transition-all hover:opacity-90"
                                    style={{ background: 'linear-gradient(135deg, #1e3a5f 0%, #2d5a87 100%)' }}
                                >
                                    Send Email
                                </a>
                            </div>
                            <button
                                onClick={() => setSubmitted(false)}
                                className="w-full text-sm text-slate-500 hover:text-slate-700"
                            >
                                ← Back to Edit
                            </button>
                        </div>
                    )}

                    <p className="mt-4 text-xs text-slate-400 text-center">
                        All submissions are reviewed before being added to the directory.
                    </p>
                </div>
            </div>
        </div>
    )
}
