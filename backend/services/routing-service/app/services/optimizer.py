from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp
from typing import List, Tuple
from core.logger import logger

class RouteOptimizer:
    def __init__(self, distance_matrix: List[List[float]]):
        self.distance_matrix = distance_matrix
        self.num_locations = len(distance_matrix)
        
    def create_data_model(
        self, 
        start_index: int = 0, 
        end_index: int = None
    ):
        """Tạo data model cho OR-Tools"""
        data = {}
        data['distance_matrix'] = self.distance_matrix
        data['num_vehicles'] = 1
        data['depot'] = start_index
        
        if end_index is not None:
            data['end'] = end_index
        else:
            data['end'] = start_index
            
        return data
    
    def solve(
        self, 
        start_index: int = 0,
        end_index: int = None,
        time_limit: int = 30
    ) -> Tuple[List[int], float]:
        """
        Giải bài toán TSP/VRP
        Returns: (order, total_distance)
        """
        data = self.create_data_model(start_index, end_index)
        
        # Tạo routing manager
        manager = pywrapcp.RoutingIndexManager(
            len(data['distance_matrix']),
            data['num_vehicles'],
            data['depot']
        )
        
        # Tạo routing model
        routing = pywrapcp.RoutingModel(manager)
        
        # Định nghĩa hàm tính khoảng cách
        def distance_callback(from_index, to_index):
            from_node = manager.IndexToNode(from_index)
            to_node = manager.IndexToNode(to_index)
            return int(data['distance_matrix'][from_node][to_node])
        
        transit_callback_index = routing.RegisterTransitCallback(distance_callback)
        routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)
        
        # Thiết lập tham số tìm kiếm
        search_parameters = pywrapcp.DefaultRoutingSearchParameters()
        search_parameters.first_solution_strategy = (
            routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
        )
        search_parameters.local_search_metaheuristic = (
            routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
        )
        search_parameters.time_limit.seconds = time_limit
        
        # Giải
        solution = routing.SolveWithParameters(search_parameters)
        
        if not solution:
            raise Exception("Không tìm thấy giải pháp tối ưu")
        
        # Lấy kết quả
        order = []
        total_distance = 0
        index = routing.Start(0)
        
        while not routing.IsEnd(index):
            node = manager.IndexToNode(index)
            order.append(node)
            previous_index = index
            index = solution.Value(routing.NextVar(index))
            total_distance += routing.GetArcCostForVehicle(
                previous_index, index, 0
            )
        
        # Thêm điểm cuối
        order.append(manager.IndexToNode(index))
        
        logger.info(f"Optimized route: {order}, distance: {total_distance}m")
        
        return order, total_distance