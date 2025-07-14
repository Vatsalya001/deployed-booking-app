"use client"

import type React from "react"
import { useState, useEffect } from "react"
import { api } from "../services/api"
import toast from "react-hot-toast"
import { Calendar, Clock, MapPin, User } from "lucide-react"

interface Event {
  id: number
  title: string
  description: string
  date: string
  duration: number
  location: string
  price: number
  max_participants: number
  current_participants: number
  facilitator_name: string
  facilitator_id: number
  type: string
}

const Events: React.FC = () => {
  const [events, setEvents] = useState<Event[]>([])
  const [loading, setLoading] = useState(true)
  const [bookingLoading, setBookingLoading] = useState<number | null>(null)
  const [filter, setFilter] = useState<string>("all")

  useEffect(() => {
    fetchEvents()
  }, [])

  const fetchEvents = async () => {
    try {
      const response = await api.get("/events")
      setEvents(response.data.events)
    } catch (error) {
      toast.error("Failed to fetch events")
    } finally {
      setLoading(false)
    }
  }

  const handleBooking = async (eventId: number) => {
    setBookingLoading(eventId)
    try {
      await api.post("/bookings", { event_id: eventId })
      toast.success("Booking successful!")
      fetchEvents() // Refresh to update participant count
    } catch (error: any) {
      toast.error(error.response?.data?.message || "Booking failed")
    } finally {
      setBookingLoading(null)
    }
  }

  const filteredEvents = events.filter((event) => {
    if (filter === "all") return true
    return event.type === filter
  })

  if (loading) {
    return (
      <div className="flex justify-center items-center min-h-screen">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow-md p-6">
        <h1 className="text-3xl font-bold text-gray-800 mb-4">Available Events</h1>

        {/* Filter Buttons */}
        <div className="flex space-x-4 mb-6">
          <button
            onClick={() => setFilter("all")}
            className={`px-4 py-2 rounded-md transition-colors ${
              filter === "all" ? "bg-blue-600 text-white" : "bg-gray-200 text-gray-700 hover:bg-gray-300"
            }`}
          >
            All Events
          </button>
          <button
            onClick={() => setFilter("session")}
            className={`px-4 py-2 rounded-md transition-colors ${
              filter === "session" ? "bg-blue-600 text-white" : "bg-gray-200 text-gray-700 hover:bg-gray-300"
            }`}
          >
            Sessions
          </button>
          <button
            onClick={() => setFilter("retreat")}
            className={`px-4 py-2 rounded-md transition-colors ${
              filter === "retreat" ? "bg-blue-600 text-white" : "bg-gray-200 text-gray-700 hover:bg-gray-300"
            }`}
          >
            Retreats
          </button>
        </div>
      </div>

      {/* Events Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredEvents.map((event) => (
          <div key={event.id} className="bg-white rounded-lg shadow-md overflow-hidden">
            <div className="p-6">
              <div className="flex items-center justify-between mb-2">
                <span
                  className={`px-2 py-1 rounded-full text-xs font-medium ${
                    event.type === "session" ? "bg-blue-100 text-blue-800" : "bg-green-100 text-green-800"
                  }`}
                >
                  {event.type}
                </span>
                <span className="text-lg font-bold text-green-600">${event.price}</span>
              </div>

              <h3 className="text-xl font-bold text-gray-800 mb-2">{event.title}</h3>
              <p className="text-gray-600 mb-4 line-clamp-3">{event.description}</p>

              <div className="space-y-2 mb-4">
                <div className="flex items-center text-sm text-gray-600">
                  <Calendar className="h-4 w-4 mr-2" />
                  {new Date(event.date).toLocaleDateString("en-US", {
                    year: "numeric",
                    month: "long",
                    day: "numeric",
                    hour: "2-digit",
                    minute: "2-digit",
                  })}
                </div>

                <div className="flex items-center text-sm text-gray-600">
                  <Clock className="h-4 w-4 mr-2" />
                  {event.duration} minutes
                </div>

                <div className="flex items-center text-sm text-gray-600">
                  <MapPin className="h-4 w-4 mr-2" />
                  {event.location}
                </div>

                <div className="flex items-center text-sm text-gray-600">
                  <User className="h-4 w-4 mr-2" />
                  {event.facilitator_name}
                </div>
              </div>

              <div className="flex items-center justify-between mb-4">
                <span className="text-sm text-gray-600">
                  {event.current_participants}/{event.max_participants} participants
                </span>
                <div className="w-full bg-gray-200 rounded-full h-2 ml-4">
                  <div
                    className="bg-blue-600 h-2 rounded-full"
                    style={{
                      width: `${(event.current_participants / event.max_participants) * 100}%`,
                    }}
                  ></div>
                </div>
              </div>

              <button
                onClick={() => handleBooking(event.id)}
                disabled={
                  event.current_participants >= event.max_participants ||
                  bookingLoading === event.id ||
                  new Date(event.date) < new Date()
                }
                className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {bookingLoading === event.id
                  ? "Booking..."
                  : event.current_participants >= event.max_participants
                    ? "Fully Booked"
                    : new Date(event.date) < new Date()
                      ? "Event Passed"
                      : "Book Now"}
              </button>
            </div>
          </div>
        ))}
      </div>

      {filteredEvents.length === 0 && (
        <div className="text-center py-12">
          <p className="text-gray-600 text-lg">No events available at the moment.</p>
        </div>
      )}
    </div>
  )
}

export default Events
