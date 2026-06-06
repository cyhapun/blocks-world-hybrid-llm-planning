(define (problem bw_easy_001)
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
    (on a b)
  )
)
