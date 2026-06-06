(define (problem bw_easy_005)
  (:domain blocks-world)

  (:objects
    a b c - block
  )

  (:init
    (on_table a)
    (on_table b)
    (on_table c)
    (clear a)
    (clear b)
    (clear c)
    (handempty)
  )

  (:goal
    (on c b)
  )
)
