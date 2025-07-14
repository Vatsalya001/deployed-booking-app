"use client"

import type React from "react"
import { useState, useEffect } from "react"
import { api } from "../services/api"
import toast from "react-hot-toast"
import { Calendar, Clock, MapPin, User, X } from "lucide-react"

interface Booking {
  id: number
  event_id: number
  event_title: string
  event_description: string
  event_date: string
  event_duration: number
  event_location: string
  event_price: number
  facilitator_name: string
  status: string
  booking_date: string
  event_type: string
}

const Bookings: React.FC = () => {
  const [bookings, setBookings] = useState<Booking[]>([])
  const [loading, setLoading] = useState(true)
  const [cancelLoading, setCancelLoading] = useState<number | null>(null)
  const [filter, setFilter] = useState<string>("all")

  useEffect(() => {
    fetchBookings()
  }, [])

  const fetchBookings = async () => {
    try {
      const response = await api.get("/bookings")
      setBookings(response.data.bookings)
    } catch (error) {
      toast.error("Failed to fetch bookings")
    } finally {
      setLoading(false)
    }
  }

  const handleCancelBooking = async (bookingId: number) => {
    if (!window.confirm("Are you sure you want to cancel this booking?")) {
      return
    }

    setCancelLoading(bookingId)
    try {
      await api.delete(`/bookings/${bookingId}`)
      toast.success("Booking cancelled successfully")
      fetchBookings()
    } catch (error: any) {
      toast.error(error.response?.data?.message || "Failed to cancel booking")
    } finally {
      setCancelLoading(null)
    }
  }

  const filteredBookings = bookings.filter((booking) => {
    const eventDate = new Date(booking.event_date)
    const now = new Date()

    if (filter === "upcoming") {
      return eventDate > now && booking.status !== "cancelled"
    } else if (filter === "past") {
      return eventDate <= now || booking.status === "cancelled"
    }
    return true
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
        <h1 className="text-3xl font-bold text-gray-800 mb-4">My Bookings</h1>

        {/* Filter Buttons */}
        <div className="flex space-x-4 mb-6">
          <button
            onClick={() => setFilter("all")}
            className={`px-4 py-2 rounded-md transition-colors ${
              filter === "all" ? "bg-blue-600 text-white" : "bg-gray-200 text-gray-700 hover:bg-gray-300"
            }`}
          >
            All Bookings
          </button>
          <button
            onClick={() => setFilter("upcoming")}
            className={`px-4 py-2 rounded-md transition-colors ${
              filter === "upcoming" ? "bg-blue-600 text-white" : "bg-gray-200 text-gray-700 hover:bg-gray-300"
            }`}
          >
            Upcoming
          </button>
          <button
            onClick={() => setFilter("past")}
            className={`px-4 py-2 rounded-md transition-colors ${
              filter === "past" ? "bg-blue-600 text-white" : "bg-gray-200 text-gray-700 hover:bg-gray-300"
            }`}
          >
            Past
          </button>
        </div>
      </div>

      {/* Bookings List */}
      <div className="space-y-4">
        {filteredBookings.map((booking) => (
          <div key={booking.id} className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center space-x-3 mb-2">
                  <h3 className="text-xl font-bold text-gray-800">{booking.event_title}</h3>
                  <span
                    className={`px-2 py-1 rounded-full text-xs font-medium ${
                      booking.event_type === "session" ? "bg-blue-100 text-blue-800" : "bg-green-100 text-green-800"
                    }`}
                  >
                    {booking.event_type}
                  </span>
                  <span
                    className={`px-3 py-1 rounded-full text-sm font-medium ${
                      booking.status === "confirmed"
                        ? "bg-green-100 text-green-800"
                        : booking.status === "pending"
                          ? "bg-yellow-100 text-yellow-800"
                          : "bg-red-100 text-red-800"
                    }`}
                  >
                    {booking.status}
                  </span>
                </div>

                <p className="text-gray-600 mb-4">{booking.event_description}</p>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                  <div className="flex items-center text-sm text-gray-600">
                    <Calendar className="h-4 w-4 mr-2" />
                    {new Date(booking.event_date).toLocaleDateString("en-US", {
                      year: "numeric",
                      month: "long",
                      day: "numeric",
                      hour: "2-digit",
                      minute: "2-digit",
                    })}
                  </div>

                  <div className="flex items-center text-sm text-gray-600">
                    <Clock className="h-4 w-4 mr-2" />
                    {booking.event_duration} minutes
                  </div>

                  <div className="flex items-center text-sm text-gray-600">
                    <MapPin className="h-4 w-4 mr-2" />
                    {booking.event_location}
                  </div>

                  <div className="flex items-center text-sm text-gray-600">
                    <User className="h-4 w-4 mr-2" />
                    {booking.facilitator_name}
                  </div>
                </div>

                <div className="flex items-center justify-between">
                  <div className="text-sm text-gray-600">
                    Booked on: {new Date(booking.booking_date).toLocaleDateString()}
                  </div>
                  <div className="text-lg font-bold text-green-600">${booking.event_price}</div>
                </div>
              </div>

              {booking.status === "confirmed" && new Date(booking.event_date) > new Date() && (
                <button
                  onClick={() => handleCancelBooking(booking.id)}
                  disabled={cancelLoading === booking.id}
                  className="ml-4 flex items-center space-x-1 text-red-600 hover:text-red-700 transition-colors disabled:opacity-50"
                >
                  <X className="h-4 w-4" />
                  <span>{cancelLoading === booking.id ? "Cancelling..." : "Cancel"}</span>
                </button>
              )}
            </div>
          </div>
        ))}
      </div>

      {filteredBookings.length === 0 && (
        <div className="text-center py-12">
          <p className="text-gray-600 text-lg">
            {filter === "upcoming"
              ? "No upcoming bookings found."
              : filter === "past"
                ? "No past bookings found."
                : "No bookings found. Start by browsing available events!"}
          </p>
        </div>
      )}
    </div>
  )
}

export default Bookings
