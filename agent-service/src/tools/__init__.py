from .station_search import search_stations, get_station_detail
from .train_query import get_train_route
from .transfer_search import search_transfer
from .isochrone import get_isochrone
from .timetable import get_station_timetable

ALL_TOOLS = {
    "search_stations": search_stations,
    "get_station_detail": get_station_detail,
    "get_train_route": get_train_route,
    "search_transfer": search_transfer,
    "get_isochrone": get_isochrone,
    "get_station_timetable": get_station_timetable,
}
